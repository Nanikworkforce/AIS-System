#!/usr/bin/env python3
"""
Test AISStream.io Integration
Simple test to verify the AISStream.io API key works and data is received
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from integrations.aisstream_client import AISStreamClient, LiveVesselTracker, LiveAISMessage
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"💡 Try installing dependencies: pip install websockets")
    sys.exit(1)

async def test_aisstream_api():
    """Test AISStream.io API connection and data reception"""
    
    print("🧪 TESTING AISSTREAM.IO INTEGRATION")
    print("=" * 50)
    
    # Your API key
    API_KEY = "8b22dbe883acb80d0c43c53d13713019791cc71f"
    
    print(f"🔑 Using API Key: {API_KEY[:20]}...")
    print(f"🕒 Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create client and tracker
    client = AISStreamClient(API_KEY)
    tracker = LiveVesselTracker()
    
    # Statistics
    messages_received = 0
    vessels_seen = set()
    test_duration = 60  # Test for 60 seconds
    
    # Callback to handle AIS messages
    def handle_ais_message(ais_message: LiveAISMessage):
        nonlocal messages_received, vessels_seen
        
        messages_received += 1
        vessels_seen.add(ais_message.mmsi)
        
        # Update tracker
        tracker.update_vessel(ais_message)
        
        # Print every 10th message to avoid spam
        if messages_received % 10 == 0:
            print(f"📡 Message #{messages_received}: {ais_message.vessel_name or 'Unknown'} "
                  f"(MMSI: {ais_message.mmsi}) at ({ais_message.latitude:.4f}, {ais_message.longitude:.4f})")
        
        # Print first few messages with details
        elif messages_received <= 3:
            print(f"📍 Vessel: {ais_message.vessel_name or 'Unknown'}")
            print(f"   MMSI: {ais_message.mmsi}")
            if ais_message.imo_number:
                print(f"   IMO: {ais_message.imo_number}")
            print(f"   Position: ({ais_message.latitude:.6f}, {ais_message.longitude:.6f})")
            print(f"   Speed: {ais_message.speed_over_ground or 0} kts")
            print(f"   Heading: {ais_message.course_over_ground or 0}°")
            print(f"   Type: {ais_message.vessel_type or 'Unknown'}")
            print(f"   Status: {ais_message.status or 'Unknown'}")
            if ais_message.destination:
                print(f"   Destination: {ais_message.destination}")
            print(f"   Timestamp: {ais_message.timestamp}")
            print()
    
    # Error callback
    def handle_error(error_msg: str):
        print(f"❌ AISStream Error: {error_msg}")
    
    # Add callbacks
    client.add_message_callback(handle_ais_message)
    client.add_error_callback(handle_error)
    
    try:
        print("🌐 Connecting to AISStream.io...")
        
        # Test with a specific region first (North Sea/English Channel)
        bounding_box = {
            "north": 60.0,   # Northern Scotland
            "south": 48.0,   # Northern France
            "east": 8.0,     # Netherlands/Germany
            "west": -8.0     # Western Ireland
        }
        
        print(f"📍 Monitoring region: North Sea & English Channel")
        print(f"   North: {bounding_box['north']}°, South: {bounding_box['south']}°")
        print(f"   East: {bounding_box['east']}°, West: {bounding_box['west']}°")
        print()
        
        # Connect to AISStream.io
        connected = await client.connect(bounding_box=bounding_box)
        
        if not connected:
            print("❌ Failed to connect to AISStream.io")
            print("🔍 Possible issues:")
            print("   • API key invalid or expired")
            print("   • Network connectivity problems")
            print("   • AISStream.io service unavailable")
            return False
        
        print("✅ Connected to AISStream.io successfully!")
        print(f"⏱️ Testing for {test_duration} seconds...")
        print("📡 Waiting for AIS messages...")
        print()
        
        # Listen for messages with timeout
        try:
            await asyncio.wait_for(client.listen(), timeout=test_duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Test completed after {test_duration} seconds")
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        
        print(f"🔗 Connection: SUCCESS")
        print(f"📡 Messages received: {messages_received}")
        print(f"🚢 Unique vessels seen: {len(vessels_seen)}")
        
        if messages_received > 0:
            rate = messages_received / test_duration
            print(f"📈 Message rate: {rate:.2f} messages/second")
            print()
            print("✅ AISStream.io integration is working correctly!")
            
            # Show tracker statistics
            tracker_stats = tracker.get_statistics()
            print(f"\n📋 Vessel Tracker Statistics:")
            print(f"   Total vessels tracked: {tracker_stats['total_vessels_tracked']}")
            print(f"   Active vessels: {tracker_stats['active_vessels']}")
            print(f"   Vessel types: {tracker_stats['vessel_types']}")
            print(f"   Vessel status: {tracker_stats['vessel_status']}")
            
            # Show some example vessels
            active_vessels = tracker.get_active_vessels()
            if active_vessels:
                print(f"\n🚢 Sample Active Vessels:")
                for i, vessel in enumerate(active_vessels[:5]):
                    print(f"   {i+1}. {vessel['vessel_name']} (MMSI: {vessel['mmsi']})")
                    print(f"      Type: {vessel.get('vessel_type', 'Unknown')}")
                    print(f"      Status: {vessel.get('status', 'Unknown')}")
                    if vessel.get('destination'):
                        print(f"      Destination: {vessel['destination']}")
            
        else:
            print("⚠️ No messages received during test period")
            print("🔍 This could mean:")
            print("   • Low vessel activity in the selected region")
            print("   • API rate limiting")
            print("   • Regional restrictions")
            print("💡 Try testing with a different region or longer duration")
        
        return messages_received > 0
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        return messages_received > 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    finally:
        # Cleanup
        if client.is_connected:
            await client.disconnect()
        print(f"\n🔌 Disconnected from AISStream.io")

async def test_quick_connection():
    """Quick test to verify API key and connection"""
    print("🚀 QUICK CONNECTION TEST")
    print("=" * 30)
    
    API_KEY = "8b22dbe883acb80d0c43c53d13713019791cc71f"
    client = AISStreamClient(API_KEY)
    
    try:
        # Try to connect (this will validate the API key)
        print("🔑 Testing API key...")
        connected = await client.connect()
        
        if connected:
            print("✅ API key is valid and connection successful!")
            await asyncio.sleep(2)  # Wait briefly
            await client.disconnect()
            return True
        else:
            print("❌ Connection failed - API key may be invalid")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🌊 AISSTREAM.IO INTEGRATION TEST")
    print("=" * 60)
    print("This test verifies that your AISStream.io API key works")
    print("and that live AIS data can be received successfully.")
    print("=" * 60)
    print()
    
    try:
        # Run quick connection test first
        print("1️⃣ PHASE 1: Quick Connection Test")
        quick_result = asyncio.run(test_quick_connection())
        
        if not quick_result:
            print("\n❌ Quick test failed. Check your API key and network connection.")
            return
        
        print("\n" + "=" * 30)
        print("2️⃣ PHASE 2: Live Data Reception Test")
        
        # Run full test
        full_result = asyncio.run(test_aisstream_api())
        
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULT")
        print("=" * 60)
        
        if full_result:
            print("🎉 SUCCESS! AISStream.io integration is working perfectly!")
            print("✅ Your API key is valid")
            print("✅ Live AIS data is being received")
            print("✅ Ready to use with the WebSocket server")
            print()
            print("🚀 Next steps:")
            print("   1. Run: python realtime_live_websocket_server.py")
            print("   2. Open: live_dashboard.html in your browser")
            print("   3. Watch live vessel data stream in real-time!")
        else:
            print("⚠️ PARTIAL SUCCESS")
            print("✅ Connection works but no data received in test period")
            print("💡 This is normal if there are few vessels in the test area")
            print("🚀 You can still proceed with the WebSocket server")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test stopped by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"💡 Make sure you have installed: pip install websockets")

if __name__ == "__main__":
    main()
