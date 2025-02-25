import logging
import docker
import re
import os  # to read env variables

def get_dns_manager_annotations():
    """
    Scan through all running Docker containers and build an annotation-like list 
    for each discovered Host(...) label (Traefik). We simulate the 'annotations' 
    dict to be consistent with the rest of the logic in batch_processor.
    """

    client = docker.from_env()
    # Regex to match Host(`something.example.com`)
    pattern = re.compile(r'Host\(`([^`]+)`\)')
    results = []

    # Read global defaults from environment variables
    default_target = os.getenv("HARBORDNS_TARGET", "dublok.com")
    default_type = os.getenv("HARBORDNS_TYPE", "CNAME")

    try:
        containers = client.containers.list()  # only running containers by default
        for container in containers:
            # Look for Traefik labels with "rule=Host(`...`)"
            for key, value in container.labels.items():
                if key.endswith(".rule") and "Host(`" in value:
                    match = pattern.search(value)
                    if match:
                        host_found = match.group(1)  # e.g., sub.example.com

                        # Container-level overrides
                        container_override_target = container.labels.get("harbordns.target")
                        container_override_type = container.labels.get("harbordns.type")

                        # Decide which target to use: container override > env variable fallback
                        used_target = container_override_target if container_override_target else default_target
                        used_type = container_override_type if container_override_type else default_type

                        # Build the dictionary with final chosen values
                        dns_manager_annotations = {
                            "harbordns/hostname": host_found,
                            "harbordns/type": used_type,
                            "harbordns/target": used_target,
                        }

                        container_data = {
                            "name": container.name,
                            "id": container.id,
                            "annotations": dns_manager_annotations
                        }

                        results.append(container_data)
                        logging.debug(
                            f"Processed container {container.name} with host: {host_found}, "
                            f"target: {used_target}, type: {used_type}"
                        )

        return results

    except Exception as e:
        logging.error(f"Failed to retrieve Docker container info: {e}")
        raise