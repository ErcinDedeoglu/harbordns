from typing import Optional, Dict, Any
import logging
from .cloudflare_client import CloudflareClient
from .cloudflare_zone import find_best_matching_zone

def delete_dns_record(
    hostname: str,
    type: str,
    existing_record: Optional[Dict[str, Any]],
    **kwargs: Any
) -> Optional[Dict[str, Any]]:
    zone_name, zone_id = find_best_matching_zone(hostname)
    
    try:
        logging.info(f"Deleting {type} record for {hostname} in zone {zone_name}")
        client = CloudflareClient.get_instance()

        logging.info(f"Existing record: {existing_record}")
        
        if not existing_record or not existing_record.result:
            logging.error(f"No existing {type} record found for {hostname}")
            return None
        
        for record in existing_record.result:
            client.dns.records.delete(zone_id=zone_id, dns_record_id=record.id)
            logging.info(f"Successfully deleted DNS record for {hostname}")
        
        return existing_record
        
    except Exception as e:
        logging.error(f"Failed to delete DNS record for {hostname}: {str(e)}")
        return None
