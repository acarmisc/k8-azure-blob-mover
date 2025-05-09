import os
import toml
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, BlobClient # Removed generate_blob_sas, Added BlobClient
from datetime import datetime, timedelta

def load_config(config_path="config.toml"):
    """Loads configuration from a TOML file."""
    try:
        with open(config_path, 'r') as f:
            config = toml.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        exit(1)
    except Exception as e:
        print(f"Error loading config file: {e}")
        exit(1)

def get_connection_strings(config):
    """Gets Azure Storage connection strings from the config object."""
    source_conn_str = config.get("source_connection_string")
    destination_conn_str = config.get("destination_connection_string")

    if not source_conn_str:
        print("Error: source_connection_string not found in config.toml.")
        exit(1)
    if not destination_conn_str:
        print("Error: destination_connection_string not found in config.toml.")
        exit(1)

    return source_conn_str, destination_conn_str

def move_blob(
    source_conn_str: str, # Changed to accept connection string
    destination_blob_client: BlobServiceClient,
    source_container_name: str,
    destination_container_name: str,
    blob_name: str,
    tag_key: str
):
    """Moves a blob from source to destination and adds a tag."""
    try:
        # Create a BlobClient for the source blob using the connection string
        source_blob_client_single = BlobClient.from_connection_string(
            conn_str=source_conn_str,
            container_name=source_container_name,
            blob_name=blob_name
        )

        # The source blob URL with SAS is directly available from the client created with a SAS connection string
        source_blob_url_with_sas = source_blob_client_single.url

        # Get a client for the destination blob
        destination_container_client = destination_blob_client.get_container_client(destination_container_name)
        destination_blob_client_single = destination_container_client.get_blob_client(blob_name)

        # Start the copy operation
        print(f"Copying blob '{blob_name}' from '{source_container_name}' to '{destination_container_name}'...")
        copy_operation = destination_blob_client_single.start_copy_from_url(source_blob_url_with_sas)

        # Wait for the copy to complete (optional, but good for small files or immediate operations)
        # For large files or long-running jobs, you might want to check status periodically
        # copy_operation.wait_for_completion()

        # Check if copy was successful (basic check, more robust error handling might be needed)
        properties = destination_blob_client_single.get_blob_properties()
        if properties.copy.status == 'success':
            print(f"Successfully copied '{blob_name}'.")

            # Tag the source blob instead of deleting it
            print(f"Tagging source blob '{blob_name}' in '{source_container_name}' with tag '{tag_key}'...")
            # Get existing tags from the source blob
            source_tags = source_blob_client_single.get_blob_tags()
            # Add or update the specific tag key for the source blob
            source_tags[tag_key] = "copied" # You can change "copied" to any desired value
            # Set the updated tags on the source blob
            source_blob_client_single.set_blob_tags(source_tags)
            print(f"Successfully tagged source blob '{blob_name}' with tag '{tag_key}'.")

        else:
            print(f"Error copying blob '{blob_name}'. Copy status: {properties.copy.status}")
            # Handle potential errors during copy
            if properties.copy.status_description:
                print(f"Copy status description: {properties.copy.status_description}")

    except Exception as e:
        print(f"An error occurred while processing blob '{blob_name}': {e}")


def main():
    config = load_config()
    source_conn_str, destination_conn_str = get_connection_strings(config)

    source_container_name = config.get("source_container_name")
    destination_container_name = config.get("destination_container_name")
    tag_key = config.get("tag_key")

    if not source_container_name or not destination_container_name or not tag_key:
        print("Error: Missing required configuration in config.toml (source_container_name, destination_container_name, or tag_key).")
        exit(1)

    try:
        # Create BlobServiceClient instance for the destination (source uses connection string directly)
        destination_blob_service_client = BlobServiceClient.from_connection_string(destination_conn_str)

        # Create a BlobServiceClient for listing source blobs (authenticated by connection string)
        source_blob_service_client_for_listing = BlobServiceClient.from_connection_string(source_conn_str)
        source_container_client = source_blob_service_client_for_listing.get_container_client(source_container_name)


        print(f"Checking blobs in container '{source_container_name}' for missing tag '{tag_key}'...")

        # List blobs and their tags
        # Note: Listing blobs with tags in a single call is more efficient if supported by the SDK/API version
        # As of azure-storage-blob 12.x, list_blobs takes include=['tags']
        blob_list = source_container_client.list_blobs(include=['tags'])

        found_blobs_to_move = []
        for blob in blob_list:
            # Check if the tag_key is NOT present in the blob's tags
            if not blob.tags or tag_key not in blob.tags:
                print(f"Found blob '{blob.name}' without tag '{tag_key}'.")
                found_blobs_to_move.append(blob.name)

        if not found_blobs_to_move:
            print("No blobs found without the specified tag.")
            return

        print(f"Found {len(found_blobs_to_move)} blob(s) to move.")

        # Ensure the destination container exists (optional, but good practice)
        try:
            destination_blob_service_client.get_container_client(destination_container_name)
        except Exception:
            print(f"Destination container '{destination_container_name}' not found. Creating...")
            destination_blob_service_client.create_container(destination_container_name)
            print(f"Destination container '{destination_container_name}' created.")


        # Move the found blobs
        for blob_name in found_blobs_to_move:
            move_blob(
                source_conn_str=source_conn_str, # Pass connection string
                destination_blob_client=destination_blob_service_client,
                source_container_name=source_container_name,
                destination_container_name=destination_container_name,
                blob_name=blob_name,
                tag_key=tag_key
            )

        print("Blob processing complete.")

    except Exception as e:
        print(f"An error occurred during the main execution: {e}")

if __name__ == "__main__":
    main()
