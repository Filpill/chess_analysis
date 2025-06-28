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

def create_instance_with_container(
    INSTANCE_NAME,
    PROJECT_ID,
    ZONE,
    CONTAINER_IMAGE,
    SUB_NET,
    SERVICE_ACCOUNT,
    MACHINE_TYPE,
    BOOT_DISK_SIZE_GB,
    BOOT_DISK_TYPE,
    SCOPES
):
    vm_initialiser_script = f"""
        gcloud compute instances create-with-container {INSTANCE_NAME} \
          --project={PROJECT_ID} \
          --zone={ZONE} \
          --machine-type={MACHINE_TYPE} \
          --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet={SUB_NET} \
          --maintenance-policy=MIGRATE \
          --provisioning-model=STANDARD \
          --service-account={SERVICE_ACCOUNT} \
          --scopes={SCOPES} \
          --image=projects/cos-cloud/global/images/cos-stable-117-18613-164-98 \
          --boot-disk-size={BOOT_DISK_SIZE_GB} \
          --boot-disk-type={BOOT_DISK_TYPE} \
          --boot-disk-device-name=instance-20250403-171730 \
          --container-image={CONTAINER_IMAGE} \
          --container-restart-policy=never \
          --container-privileged \
          --no-shielded-secure-boot \
          --shielded-vtpm \
          --shielded-integrity-monitoring \
          --labels=goog-ec-src=vm_add-gcloud,container-vm=cos-stable-117-18613-164-98
      """

    runner = subprocess.run(["bash", "-c", vm_initialiser_script], capture_output=True, text=True)
    return runner
