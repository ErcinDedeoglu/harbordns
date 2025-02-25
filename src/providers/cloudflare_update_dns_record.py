import logging
from typing import Optional, Dict, Any
from .cloudflare_client import CloudflareClient
from .cloudflare_zone import find_best_matching_zone

def update_dns_record(
    hostname: str,
    target: str,
    type: str,
    ttl: int,
    existing_record: Optional[Dict[str, Any]],
    **kwargs: Any
) -> Optional[Dict[str, Any]]:
    try:
        # First find the existing record
        zone_name, zone_id = find_best_matching_zone(hostname)
        logging.debug(f"#### Existing record: {existing_record}")

        if not existing_record or not existing_record.result:
            logging.error(f"No existing {type} record found for {hostname}")
            return None

        first_record = existing_record.result[0]
        proxied = kwargs.get('proxied', False)
        
        # If record is proxied, TTL will always be 1 (auto)
        effective_ttl = 1 if proxied else ttl
        
        # Compare current values with new values
        if (first_record.content == target and 
            first_record.type == type and
            first_record.proxied == proxied and
            (first_record.ttl == effective_ttl)):
            logging.info(f"No changes needed for {hostname} DNS record - skipping update")
            return existing_record

        # Log what's changing
        changes = []
        if first_record.content != target:
            changes.append(f"content: {first_record.content} -> {target}")
        if first_record.type != type:
            changes.append(f"type: {first_record.type} -> {type}")
        if first_record.proxied != proxied:
            changes.append(f"proxied: {first_record.proxied} -> {proxied}")
        if first_record.ttl != effective_ttl:
            changes.append(f"ttl: {first_record.ttl} -> {effective_ttl}")

        if not changes:
            logging.info(f"No changes needed for {hostname} DNS record - skipping update")
            return existing_record
            
        record_id = first_record.id
        logging.info(f"Updating {type} record for {hostname} in zone {zone_name}")
        logging.info(f"Changes to be made: {', '.join(changes)}")

        # Update the record using the 'edit' method
        client = CloudflareClient.get_instance()
        result = client.dns.records.edit(
            zone_id=zone_id,
            dns_record_id=record_id,
            name=hostname,
            type=type,
            content=target,
            ttl=effective_ttl,
            proxied=proxied
        )

        logging.info(f"Successfully updated DNS record for {hostname}")
        logging.debug(f"Updated record: {result}")
        return result

    except Exception as e:
        logging.error(f"Failed to update DNS record for {hostname}: {str(e)}")
        return None