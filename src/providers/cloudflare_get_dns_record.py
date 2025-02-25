from typing import Optional, List, Dict, Any
from .cloudflare_client import CloudflareClient
from .cloudflare_zone import find_best_matching_zone
import logging

def get_dns_record_by_hostname_and_type(
    hostname: str,
    type: str,
    **kwargs: Any
) -> Optional[List[Dict[str, Any]]]:
    zone_name, zone_id = find_best_matching_zone(hostname)
    logging.info(f"Found matching zone: {zone_name} (ID: {zone_id}) for hostname: {hostname}")

    try:
        client = CloudflareClient.get_instance()
        records = client.dns.records.list(zone_id=zone_id, name=hostname, type=type)
        logging.info(f"Records for {hostname}: {records}")
        return records
    except Exception as e:
        logging.error(f"Failed to fetch records for {hostname}: {str(e)}")
        return None
