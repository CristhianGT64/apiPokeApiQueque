import json 
import logging

from fastapi import HTTPException
from models.PokeRequest import PokemonRequest
from utils.database import execute_query_json
from utils.AQueue import AQueue
from utils.ABlob import ABlob


# configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def select_pokemon_request( id: int ):
    try:
        query = "select * from pokequeue.requests where id = ?"
        params = (id,)
        result = await execute_query_json( query , params )
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error( f"Error selecting report request {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )


async def update_pokemon_request( pokemon_request: PokemonRequest) -> dict:
    try:
        query = " exec pokequeue.update_poke_request ?, ?, ? "
        if not pokemon_request.url:
            pokemon_request.url = "";

        params = ( pokemon_request.id, pokemon_request.status, pokemon_request.url  )
        result = await execute_query_json( query , params, True )
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error( f"Error updating report request {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )


async def insert_pokemon_request( pokemon_request: PokemonRequest) -> dict:
    try:
        query = " exec pokequeue.create_poke_request ? "
        params = ( pokemon_request.pokemon_type,  )
        result = await execute_query_json( query , params, True )
        result_dict = json.loads(result)

        await AQueue().insert_message_on_queue( result )

        return result_dict
    except Exception as e:
        logger.error( f"Error inserting report reques {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error" )


async def get_all_request() -> dict:
    query = """
        select 
            r.id as ReportId
            , s.description as Status
            , r.type as PokemonType
            , r.url 
            , r.created 
            , r.updated
        from pokequeue.requests r 
        inner join pokequeue.status s 
        on r.id_status = s.id 
    """
    result = await execute_query_json( query  )
    result_dict = json.loads(result)
    blob = ABlob()
    for record in result_dict:
        id = record['ReportId']
        record['url'] = f"{record['url']}?{blob.generate_sas(id)}"
    return result_dict

async def delete_pokemon_request( id: int ) -> dict:
    try:
        # Verificar si el request existe antes de eliminar
        query_check = "select * from pokequeue.requests where id = ?"
        params_check = (id,)
        result_check = await execute_query_json( query_check , params_check )
        result_check_dict = json.loads(result_check)
        if not result_check_dict:
            raise HTTPException( status_code=404 , detail="No se encontro el reporte" )
        
        # Intentar borrar el blob del contenedor Azure Blob Storage
        try:
            blob = ABlob()
            blob_deleted = blob.delete_blob(id)
            if blob_deleted:
                logger.info(f"Blob poke_report_{id}.csv eliminado correctamente de Azure Blob Storage.")
            else:
                logger.warning(f"El blob poke_report_{id}.csv no se encontró en Azure Blob Storage.")
        except Exception as blob_error:
            logger.error(f"Error al eliminar el blob del contenedor: {blob_error}")
            # No interrumpimos el flujo, continuamos con el borrado de BD

        # Borrar el registro de la base de datos
        query = " exec pokequeue.sp_EliminarReportePorId ? "
        params = ( id , )
        result = await execute_query_json( query , params, True )
        result_dict = json.loads(result)
        logger.info(f"Registro {id} eliminado correctamente de la base de datos.")
        return result_dict
    except Exception as e:
        logger.error( f"Error deleting report request {e}" )
        raise HTTPException( status_code=500 , detail="Internal Server Error eliminar" )