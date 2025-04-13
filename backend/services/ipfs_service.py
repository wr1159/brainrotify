import json
import httpx
import os
import asyncio
from pathlib import Path
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

class IPFSService:
    def __init__(self):
        # Using Pinata as the IPFS service
        self.pinata_upload_url = "https://uploads.pinata.cloud/v3/files"
        self.pinata_json_url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        
        # Get JWT from environment variable
        self.pinata_jwt = os.environ.get("PINATA_JWT")
        self.logger = logging.getLogger(__name__)
        
        # Mode check
        self.use_mock = not self.pinata_jwt
        if self.use_mock:
            self.logger.warning("PINATA_JWT not found in environment. Using mock mode for IPFS uploads.")
        else:
            self.logger.info("Using Pinata for IPFS uploads")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_file(self, file_path, name=None, keyvalues=None):
        """Upload a file to IPFS using Pinata and return the IPFS hash (CID).
        
        Args:
            file_path (str): The path to the file to upload
            name (str, optional): Custom name for the file
            keyvalues (dict, optional): Metadata key-values for the file
            
        Returns:
            str: The IPFS URI (ipfs://<CID>) of the uploaded file
        """
        if self.use_mock:
            # Mock response for demo purposes
            return f"ipfs://Qm{Path(file_path).name.replace('.', '')[:32]}"
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Prepare headers with JWT
            headers = {
                "Authorization": f"Bearer {self.pinata_jwt}"
            }
            
            # Prepare files and data for multipart upload
            file_name = name or file_path.name
            
            # Prepare the multipart form data
            form_data = {"network": "public"}
            if keyvalues:
                form_data["keyvalues"] = json.dumps(keyvalues)
                
            files = {
                "file": (file_name, open(file_path, "rb"))
            }
            
            # Use httpx for async file upload
            async with httpx.AsyncClient(timeout=60.0) as client:
                self.logger.info(f"Uploading file {file_path} to Pinata...")
                response = await client.post(
                    self.pinata_upload_url,
                    headers=headers,
                    data=form_data,
                    files=files
                )
                
                # Close the file handle
                files["file"][1].close()
                
                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                    raise Exception(f"Pinata upload failed: {response.status_code} - {response.text}")
                
                # Parse response
                result = response.json()
                if "data" not in result or "cid" not in result["data"]:
                    raise ValueError(f"Unexpected Pinata response format: {result}")
                
                cid = result["data"]["cid"]
                self.logger.info(f"File uploaded successfully with CID: {cid}")
                return f"https://apricot-defensive-vole-912.mypinata.cloud/ipfs/{cid}"
                # return f"ipfs://{cid}"
                
        except Exception as e:
            self.logger.error(f"Error uploading file to IPFS: {str(e)}")
            if not self.use_mock:
                # If we're not in mock mode, re-raise the exception
                raise
            # In mock mode, return a mock CID
            return f"ipfs://Qm{Path(file_path).name.replace('.', '')[:32]}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_json(self, metadata):
        """Upload JSON metadata to IPFS using Pinata.
        
        Args:
            metadata (dict): The metadata to upload
            
        Returns:
            str: The IPFS URI (ipfs://<CID>) of the uploaded metadata
        """
        if self.use_mock:
            # Mock response for demo purposes
            metadata_str = json.dumps(metadata)
            mock_hash = hex(hash(metadata_str) % 10**32)[2:]
            return f"ipfs://Qm{mock_hash[:32]}"
        
        try:
            # Prepare headers with JWT
            headers = {
                "Authorization": f"Bearer {self.pinata_jwt}",
                "Content-Type": "application/json"
            }
            
            # Use httpx for async JSON upload
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.logger.info("Uploading JSON metadata to Pinata...")
                response = await client.post(
                    self.pinata_json_url,
                    headers=headers,
                    json={
                        "pinataContent": metadata
                    }
                )
                
                # Check response
                if response.status_code != 200:
                    self.logger.error(f"Pinata JSON upload failed: {response.status_code} - {response.text}")
                    raise Exception(f"Pinata JSON upload failed: {response.status_code} - {response.text}")
                
                # Parse response
                result = response.json()
                if "IpfsHash" not in result:
                    raise ValueError(f"Unexpected Pinata response format: {result}")
                
                cid = result["IpfsHash"]
                self.logger.info(f"JSON uploaded successfully with CID: {cid}")
                return f"https://apricot-defensive-vole-912.mypinata.cloud/ipfs/{cid}"
                # return f"ipfs://{cid}"
                
        except Exception as e:
            self.logger.error(f"Error uploading JSON to IPFS: {str(e)}")
            if not self.use_mock:
                # If we're not in mock mode, re-raise the exception
                raise
            # In mock mode, return a mock CID
            metadata_str = json.dumps(metadata)
            mock_hash = hex(hash(metadata_str) % 10**32)[2:]
            return f"ipfs://Qm{mock_hash[:32]}"
    
    def create_metadata(self, content, style, video_ipfs_uri, thumbnail_ipfs_uri , ticker, description):
        """Create metadata for the NFT.
        
        Args:
            content (str): The topic of the video
            style (str): The style of the brainrot content
            video_ipfs_uri (str): The IPFS URI of the video
            thumbnail_ipfs_uri (str, optional): The IPFS URI of the thumbnail image
            ticker (str, optional): Ticker symbol for the NFT
            description (str, optional): Description of the video
            
        Returns:
            dict: The metadata for the NFT
        """
        metadata = {
            "name": ticker,
            "description": description,
            "symbol": ticker,
            "image": thumbnail_ipfs_uri,
            "animation_url": video_ipfs_uri,
            "content": {
                "uri": video_ipfs_uri,
                "mime": "video/mp4"
            },
        }
        
        
        return metadata 