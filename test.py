import json

import functions_framework
from google.cloud import bigquery

# --- 1. CONFIGURATION: UPDATE THESE ---
BIGQUERY_PROJECT = "data-engineering-ai-472818"  # Your Google Cloud project ID
BIGQUERY_DATASET = "spotify_data"  # The BigQuery dataset you created
BIGQUERY_TABLE = "spotify_playlists"  # The table you want to load data into
# ----------------------------------------

# Initialize the BigQuery client
bigquery_client = bigquery.Client()


@functions_framework.http
def gcs_bq_loading_cf(request):
    """
    Receives an Eventarc Audit Log event from GCS,
    and orchestrates a BigQuery load job from that file.
    """

    # 1. Get the event data
    try:
        event_data = request.get_json()
        if not event_data:
            print("No event data received.")
            return "Bad Request: No event data", 400

        print("--- Event Data Received ---")
        print(json.dumps(event_data, indent=2))
        print("---------------------------")

        # 2. Extract the bucket and file name from the AuditLog
        resource_name = event_data["protoPayload"]["resourceName"]

        parts = resource_name.split("/")
        bucket_name = parts[3]
        object_name = "/".join(parts[5:])  # e.g., "input/spotify_playlist.csv"

        print(f"Parsed info: bucket='{bucket_name}', file='{object_name}'")

        # 3. Configure and run the BigQuery Load Job

        # Create the full GCS URI
        gcs_uri = f"gs://{bucket_name}/{object_name}"

        # Create the full BigQuery table ID
        table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            # Specify the source format
            source_format=bigquery.SourceFormat.CSV,
            # Skip the header row (common in CSVs)
            skip_leading_rows=1,
            # Let BigQuery detect the schema
            autodetect=True,
            # Append to the table (or use WRITE_TRUNCATE to overwrite)
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        print(f"Starting BigQuery load job from '{gcs_uri}' into '{table_id}'...")

        # Start the load job
        load_job = bigquery_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)

        # Wait for the job to complete
        load_job.result()

        print("BigQuery load job finished successfully.")

        # 5. Return "OK" to acknowledge the event
        return "OK", 200

    except KeyError as e:
        print(f"Error parsing event: missing key {e}")
        return "OK", 200  # Acknowledge to prevent retry
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Internal Server Error", 500
