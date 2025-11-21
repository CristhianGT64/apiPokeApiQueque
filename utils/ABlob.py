import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_SAK")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")

class ABlob:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)

    def generate_sas(self, id: int):
        blob_name = f"poke_report_{id}.csv"
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=AZURE_STORAGE_CONTAINER,
            blob_name=blob_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        return sas_token

    def delete_blob(self, id: int) -> bool:
        """
        Elimina el archivo CSV correspondiente del contenedor Azure Blob Storage.
        
        Args:
            id (int): ID del reporte (se usa para construir el nombre poke_report_{id}.csv)
        
        Returns:
            bool: True si se eliminó correctamente, False si el blob no existe.
        
        Raises:
            Exception: Si ocurre un error durante la eliminación.
        """
        blob_name = f"poke_report_{id}.csv"
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=AZURE_STORAGE_CONTAINER,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True
        except Exception as e:
            # Capturar ResourceNotFoundError de forma genérica
            if "BlobNotFound" in str(type(e).__name__) or "404" in str(e):
                return False
            raise