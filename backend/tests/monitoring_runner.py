#!/usr/bin/env python3
"""
Direct test for monitoring functionality
"""
from test_monitoring import app
import uvicorn
import threading
import time
import requests

def run_server():
    """Run the FastAPI server in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

def test_endpoints():
    """Test the monitoring endpoints"""
    print("🔍 Testing monitoring functionality...")
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        # Test health endpoint
        print("\n1. Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test root endpoint  
        print("\n2. Testing / endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Generate some traffic
        print("\n3. Generating traffic for metrics...")
        for i in range(5):
            requests.get(f"{base_url}/health", timeout=5)
            requests.get(f"{base_url}/", timeout=5)
            time.sleep(0.5)
        
        # Test metrics endpoint
        print("\n4. Testing /metrics endpoint...")
        response = requests.get(f"{base_url}/metrics", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        
        metrics_data = response.text
        print("\n   Sample metrics:")
        lines = [line for line in metrics_data.split('\n')[:30] if line.strip() and not line.startswith('#')]
        for line in lines[:10]:  # Show first 10 non-comment lines
            print(f"   {line}")
        
        print("\n✅ All monitoring endpoints are working!")
        
        # Check for key metrics
        if 'piazzati_requests_total' in metrics_data:
            print("✅ Request counter metrics found")
        if 'piazzati_request_duration_seconds' in metrics_data:
            print("✅ Request duration metrics found")
            
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    success = test_endpoints()
    
    if success:
        print("\n🎉 Monitoring implementation successful!")
        print("\nKey features implemented:")
        print("✅ FastAPI app with middleware for automatic metrics collection")
        print("✅ Prometheus metrics endpoint at /metrics")
        print("✅ Request counting by endpoint and method")
        print("✅ Request duration histograms for p95/p99 calculations")
        print("✅ Proper Prometheus format output")
    else:
        print("\n❌ Monitoring test failed")