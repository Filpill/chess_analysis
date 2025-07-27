def append_prefix_to_gcs_files(prefix, excluded_prefixes, logger):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    
    # The for loop will exlude any files that should not be targeted in the renaming
    for blob in blobs:
        if any(blob.name.startswith(f"{prefix}/") for prefix in excluded_prefixes):
            logger.info("Skipping {blob.name} | Excluded from renaming process")
            continue

        new_name = f"{prefix}/{blob.name}"
        bucket.rename_blob(blob, new_name)
        logger.info(f"Renamed {blob.name} -> {new_name}") 


def rename_prefix_of_gcs_files(bucket_name, old_prefix, new_prefix):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=old_prefix)

    for blob in blobs:
        new_name = blob.name.replace(old_prefix, new_prefix, 1)
        new_blob = bucket.copy_blob(blob, bucket, new_name)
        blob.delete()
        print(f"Renamed {blob.name} -> {new_name}")
