from datetime import datetime
import logging
import time
from providers.cloudflare_get_dns_record import get_dns_record_by_hostname_and_type
from providers.cloudflare_create_dns_record import create_dns_record
from providers.cloudflare_delete_dns_record import delete_dns_record
from providers.cloudflare_update_dns_record import update_dns_record
from .dns_action import ActionType, DNSAction, DNSActionQueue
from .docker_helper import get_dns_manager_annotations

previous_dns_manager_annotations = None

dns_action_queue = DNSActionQueue()

def initializer():
    logging.info("Initializing batch processor")    
    while True:
        task()
        time.sleep(10)

def task():
    global previous_dns_manager_annotations
    current_dns_manager_annotations = get_dns_manager_annotations()
    
    compare_data(previous_dns_manager_annotations, current_dns_manager_annotations)
    
    ready_actions = dns_action_queue.get_ready_actions(30)
    if ready_actions:
        for action in ready_actions:
            process_action(action)
    
    previous_dns_manager_annotations = current_dns_manager_annotations

def compare_data(previous_annotations, current_annotations):
    current_time = datetime.now()
    
    if not previous_annotations:
        logging.info("No previous data available. Treating all records as new.")
        for record in current_annotations:
            action = create_dns_action(ActionType.ADD, record, current_time)
            dns_action_queue.add_action(action)
        return True
    
    has_changes = False
    
    prev_dict = create_annotation_dict(previous_annotations)
    curr_dict = create_annotation_dict(current_annotations)
    
    for key, curr_record in curr_dict.items():
        if key not in prev_dict:
            action = create_dns_action(ActionType.ADD, curr_record, current_time)
            dns_action_queue.add_action(action)
            has_changes = True
        else:
            prev_record = prev_dict[key]
            if records_differ(prev_record, curr_record):
                action = create_dns_action(ActionType.MODIFY, curr_record, current_time, prev_record=prev_record)
                dns_action_queue.add_action(action)
                has_changes = True
    
    for key, prev_record in prev_dict.items():
        if key not in curr_dict:
            action = create_dns_action(ActionType.DELETE, None, current_time, prev_record=prev_record)
            dns_action_queue.add_action(action)
            has_changes = True
    
    return has_changes

def create_annotation_dict(annotations):
    return {
        (record.get('annotations', {}).get('harbordns/hostname'),
         record.get('annotations', {}).get('harbordns/type')): record
        for record in annotations
    }

def records_differ(prev_record, curr_record):
    prev_fields = get_record_fields(prev_record)
    curr_fields = get_record_fields(curr_record)
    return prev_fields != curr_fields

def get_record_fields(record):
    annotations = record.get('annotations', {})
    return {
        'provider': annotations.get('harbordns/provider', 'cloudflare'),
        'target': annotations.get('harbordns/target', record.get('target', '')),
        'ttl': annotations.get('harbordns/ttl', '300'),
        'proxied': annotations.get('harbordns/cloudflare.proxied', 'false')
    }

def create_dns_action(action_type, record, timestamp, prev_record=None):
    if action_type == ActionType.DELETE:
        if prev_record is None:
            raise ValueError("Previous record must be provided for DELETE actions.")
        base_record = prev_record
    else:
        if record is None:
            raise ValueError("Current record must be provided for ADD and MODIFY actions.")
        base_record = record
    
    hostname = get_dns_manager_annotation(base_record, "hostname")
    provider = get_dns_manager_annotation(base_record, "provider", "cloudflare")
    target = get_dns_manager_annotation(base_record, "target")
    ttl = get_dns_manager_annotation(base_record, "ttl", "1")
    proxied = get_dns_manager_annotation(base_record, "cloudflare.proxied", "true")
    type = get_dns_manager_annotation(base_record, "type")
    
    logging.info(f"Creating DNS action: {action_type} {hostname} ({type}, {target}, {ttl}, {proxied})")
    
    return DNSAction(
        timestamp=timestamp,
        action_type=action_type,
        hostname=hostname,
        type=type,
        record_data=base_record,
        previous_data=prev_record if action_type == ActionType.MODIFY else None,
        provider=provider,
        target=target,
        ttl=ttl,
        proxied=proxied
    )

def get_dns_manager_annotation(record, annotation, default=None):
    return record.get('annotations', {}).get(f"harbordns/{annotation}", default)

def process_action(action):
    logging.info(f"[process_action] action: {action}")
    
    existing_record = get_dns_record_by_hostname_and_type(action.hostname, action.type)
    ttl_int = int(action.ttl)
    
    if action.action_type in [ActionType.MODIFY, ActionType.ADD]:
        if existing_record.result:
            update_dns_record(
                hostname=action.hostname,
                target=action.target,
                type=action.type,
                ttl=ttl_int,
                proxied=action.proxied,
                existing_record=existing_record
            )
        else:
            create_dns_record(
                hostname=action.hostname,
                target=action.target,
                type=action.type,
                ttl=ttl_int,
                proxied=action.proxied
            )
    elif action.action_type == ActionType.DELETE:
        if existing_record.result:
            delete_dns_record(
                hostname=action.hostname,
                type=action.type,
                existing_record=existing_record
            )
        else:
            logging.info(f"No existing record found for {action.hostname} ({action.type})")