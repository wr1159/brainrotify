import json
import httpx
from pathlib import Path

class IPFSService:
    def __init__(self):
        # Using Pinata as the IPFS service
        self.pinata_api_url = "https://api.pinata.cloud/pinning"
        self.pinata_api_key = None
        self.pinata_secret_api_key = None
        
        # TODO: Update to production mode
        self.use_mock = True
    
    async def upload_file(self, file_path):
        """Upload a file to IPFS and return the IPFS hash (CID).
        
        Args:
            file_path (Path): The path to the file to upload
            
        Returns:
            str: The IPFS hash (CID) of the uploaded file
        """
        if self.use_mock:
            # Mock response for demo purposes
            return f"ipfs://Qm{Path(file_path).name.replace('.', '')[:32]}"
        
        # In a real implementation, you'd use something like this:
        file_name = Path(file_path).name
        
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as file_data:
                files = {"file": (file_name, file_data)}
                headers = {
                    "pinata_api_key": self.pinata_api_key,
                    "pinata_secret_api_key": self.pinata_secret_api_key
                }
                
                response = await client.post(
                    f"{self.pinata_api_url}/pinFileToIPFS",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                ipfs_hash = response.json().get("IpfsHash")
                return f"ipfs://{ipfs_hash}"
    
    async def upload_json(self, metadata):
        """Upload JSON metadata to IPFS.
        
        Args:
            metadata (dict): The metadata to upload
            
        Returns:
            str: The IPFS hash (CID) of the uploaded metadata
        """
        if self.use_mock:
            # Mock response for demo purposes
            metadata_str = json.dumps(metadata)
            mock_hash = hex(hash(metadata_str) % 10**32)[2:]
            return f"ipfs://Qm{mock_hash[:32]}"
        
        # In a real implementation, you'd use something like this:
        async with httpx.AsyncClient() as client:
            headers = {
                "pinata_api_key": self.pinata_api_key,
                "pinata_secret_api_key": self.pinata_secret_api_key,
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{self.pinata_api_url}/pinJSONToIPFS",
                headers=headers,
                json=metadata
            )
            response.raise_for_status()
            ipfs_hash = response.json().get("IpfsHash")
            return f"ipfs://{ipfs_hash}"
    
    def create_metadata(self, content, style, video_ipfs_uri):
        """Create metadata for the NFT.
        
        Args:
            content (str): The topic of the video
            style (str): The style of the brainrot content
            video_ipfs_uri (str): The IPFS URI of the video
            
        Returns:
            dict: The metadata for the NFT
        """
        metadata = {
            "name": f"Brainrotify: {content} - {style}",
            "description": f"A brainrot video about {content} in the style of {style}",
            "image": video_ipfs_uri,  # This should ideally be a thumbnail
            "animation_url": video_ipfs_uri,
            "attributes": [
                {
                    "trait_type": "Content",
                    "value": content
                },
                {
                    "trait_type": "Style",
                    "value": style
                },
                {
                    "trait_type": "Generator",
                    "value": "Brainrotify"
                }
            ]
        }
        
        return metadata 