import os
import uuid
import boto3
import paramiko
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)



class FileManager:

    def push_file(self, file_path, local_config, destination_config):
        """
        Push a file to a remote destination.
        
        Args:
            file_path: Path to the file to push
            local_config: Local configuration
            destination_config: Destination configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = True
        location_type = destination_config.type
        
        if not location_type:
            logger.error("Missing 'type' in destination configuration")
            return False
            
        source_path = os.path.join(local_config.path, file_path)
        dest_path = os.path.join(destination_config.path, file_path)
        
        # Check if source file exists
        if not os.path.exists(source_path):
            logger.error(f"Source file not found: {source_path}")
            return False
        
        try:
            # Handle different destination types
            if location_type == "scp":
                # Implementation for SCP destination
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        destination_config.host,
                        username=destination_config.user,
                        key_filename=destination_config.identity_file,
                    )
                    
                    # Create destination directory
                    dest_dir = os.path.dirname(dest_path)
                    ssh.exec_command(f"mkdir -p {dest_dir}")
                    
                    # Transfer file
                    sftp = ssh.open_sftp()
                    sftp.put(source_path, dest_path)
                    sftp.close()
                    ssh.close()
                    logger.info(f"File {file_path} successfully pushed to SCP host {destination_config.host}")
                except Exception as e:
                    logger.error(f"SCP error for {file_path}: {e}")
                    success = False
                    
            elif location_type == "s3":
                # Implementation for S3 destination
                try:
                    s3 = boto3.client(
                        "s3",
                        aws_access_key_id=destination_config.aws_access_key_id,
                        aws_secret_access_key=destination_config.aws_secret_access_key,
                    )
                    
                    s3_path = dest_path
                    if s3_path.startswith('/'):
                        s3_path = s3_path[1:]  # Remove leading slash for S3 keys
                        
                    s3.upload_file(
                        source_path, 
                        destination_config.bucket,
                        s3_path
                    )
                    logger.info(f"File {file_path} successfully pushed to S3 bucket {destination_config.bucket}")
                except Exception as e:
                    logger.error(f"S3 error for {file_path}: {e}")
                    success = False
                    
            else:
                logger.error(f"Unsupported destination type: {location_type}")
                success = False
                    
        except Exception as e:
            logger.error(f"Remote push error: {str(e)}")
            success = False
            
        return success

    def pull_file(self, file_path, source_config, local_config):
        """
        Pull a file from a remote source.
        
        Args:
            file_path: Path to the file to pull
            source_config: Source configuration
            local_config: Local configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = True
        location_type = source_config.type
        
        if not location_type:
            logger.error("Missing 'type' in source configuration")
            return False
            
        local_base_path = local_config.path
        if not local_base_path:
            logger.error("No local path specified in local_config")
            return False
            
        local_path = os.path.join(local_base_path, file_path)
        local_dir = os.path.dirname(local_path)
        
        # Ensure the directory exists
        try:
            os.makedirs(local_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create directory {local_dir}: {e}")
            return False
            
        try:
            if location_type == "scp":
                # Implementation for SCP source
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        hostname=source_config.host,
                        username=source_config.user,
                        key_filename=source_config.identity_file,
                        timeout=30
                    )
                    
                    # Construct remote path
                    file_name = os.path.basename(file_path)
                    remote_path = os.path.join(source_config.path, file_path)
                    
                    # Download file
                    sftp = ssh.open_sftp()
                    sftp.get(remote_path, local_path)
                    sftp.close()
                    ssh.close()
                    
                    logger.info(f"Successfully pulled file {file_path} from SCP host {source_config.host}")
                except Exception as e:
                    logger.error(f"SCP error for {file_path}: {e}")
                    success = False
                    
            elif location_type == "s3":
                # Implementation for S3 source
                try:
                    s3 = boto3.client(
                        "s3",
                        aws_access_key_id=source_config.aws_access_key_id,
                        aws_secret_access_key=source_config.aws_secret_access_key,
                        region_name=source_config.get("region_name")
                    )
                    
                    # Construct S3 key path
                    s3_path = file_path
                    if s3_path.startswith('/'):
                        s3_path = s3_path[1:]  # Remove leading slash for S3 keys
                        
                    s3.download_file(
                        source_config.bucket, 
                        s3_path, 
                        local_path
                    )
                    
                    logger.info(f"Successfully pulled file {file_path} from S3 bucket {source_config.bucket}")
                except Exception as e:
                    logger.error(f"S3 error for {file_path}: {e}")
                    success = False
                    
            else:
                logger.error(f"Unsupported source type: {location_type}")
                success = False
                    
        except Exception as e:
            logger.error(f"Remote pull error: {str(e)}")
            success = False
            
        return success
        
    def get_new_uuid(self):
        return str(uuid.uuid4())
    
    def get_path_from_uuid(self,uuid):
        return os.path.join(uuid[:8],uuid)


    


