import weaviate
from weaviate.classes.init import Auth

# Connect to Weaviate Cloud (v4 syntax)
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://v1o3l1nntqc4lpd0f8ecw.c0.asia-southeast1.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key("L1QwTmVMM2NPeTVXQnN6VF9MeDBkNnlnNUMwbnJEVGMyOEFzL0JhUVJiT3dUQ0dsaHVsa0NjdFdWcmt3PV92MjAw"),
    headers={"X-Cohere-Api-Key": "LX7fUojKOyLgRSXYnOe151SWCeHnAKEomt0KXH3l"}
)

try:
    # Check if Document collection exists
    if client.collections.exists("Document"):
        collection = client.collections.get("Document")
        
        # Get total count
        result = collection.aggregate.over_all(total_count=True)
        print(f"✅ Total documents: {result.total_count}")
        
        # Get sample document
        if result.total_count > 0:
            sample = collection.query.fetch_objects(limit=1)
            print(f"\n📄 Sample document:")
            print(sample.objects[0].properties)
    else:
        print("❌ Document collection doesn't exist")
        
finally:
    client.close()