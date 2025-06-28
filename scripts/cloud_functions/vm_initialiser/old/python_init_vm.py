def python_create_instance_with_container(
    instance_name,
    project_id,
    zone,
    container_image,
    subnet,
    service_account,
    machine_type,
    boot_disk_size_gb,
    boot_disk_type,
    scopes
):
    credentials, _ = default()
    compute = discovery.build("compute", "v1", credentials=credentials)

    # Sanitize instance name
    instance_name = instance_name.replace("_", "-")
    region = "-".join(zone.split("-")[:-1])  # e.g., europe-west1-c → europe-west1

    # ✅ Correctly formatted, unindented YAML string
    container_declaration = f"""spec:
  containers:
    - name: {instance_name}
      image: {container_image}
      command: ["python3", "/app/main.py"]
      stdin: false
      tty: false
  restartPolicy: Never"""

    config = {
        "name": instance_name,
        "machineType": f"zones/{zone}/machineTypes/{machine_type}",
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": "projects/cos-cloud/global/images/cos-stable-117-18613-164-98",
                    "diskSizeGb": boot_disk_size_gb,
                    "diskType": f"zones/{zone}/diskTypes/{boot_disk_type}"
                },
                "deviceName": instance_name
            }
        ],
        "networkInterfaces": [
            {
                "subnetwork": f"regions/{region}/subnetworks/{subnet}",
                "stackType": "IPV4_ONLY",
                "networkTier": "PREMIUM"
            }
        ],
        "serviceAccounts": [
            {
                "email": service_account,
                "scopes": scopes
            }
        ],
        "scheduling": {
            "onHostMaintenance": "MIGRATE",
            "provisioningModel": "STANDARD"
        },
        "labels": {
            "goog-ec-src": "vm_add-gcloud",
            "container-vm": "cos-stable-117-18613-164-98"
        },
        "shieldedInstanceConfig": {
            "enableSecureBoot": False,
            "enableVtpm": True,
            "enableIntegrityMonitoring": True
        },
        "advancedMachineFeatures": {
            "enableNestedVirtualization": False
        },
        "metadata": {
            "items": [
                {
                    "key": "gce-container-declaration",
                    "value": container_declaration
                },
                {
                    "key": "serial-port-logging-enable",
                    "value": "true"
                }
            ]
        }
    }

    print("Sending container declaration:\n", container_declaration)  # 🧪 Optional debug

    request = compute.instances().insert(
        project=project_id,
        zone=zone,
        body=config
    )

    response = request.execute()
    return response
