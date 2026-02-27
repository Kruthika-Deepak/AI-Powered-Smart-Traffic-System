import requests
import sys
from datetime import datetime

class BangaloreTrafficAPITester:
    def __init__(self, base_url="https://urban-pulse-18.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_keys=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            response_data = {}
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                except:
                    response_data = {}

            if success:
                # Check for expected keys if provided (only for dict responses)
                if expected_keys and isinstance(response_data, dict):
                    for key in expected_keys:
                        if key not in response_data:
                            success = False
                            print(f"❌ Failed - Missing expected key: {key}")
                            break
                
                if success:
                    self.tests_passed += 1
                    print(f"✅ Passed - Status: {response.status_code}")
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response_data:
                    print(f"   Error: {response_data}")
                self.failed_tests.append(f"{name}: {response.status_code} - {response_data}")

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200,
            expected_keys=["message", "version"]
        )

    def test_locations_endpoint(self):
        """Test locations endpoint"""
        success, response = self.run_test(
            "Locations Endpoint",
            "GET",
            "locations",
            200
        )
        
        if success:
            if isinstance(response, list) and len(response) == 4:
                print(f"   ✅ Found 4 locations as expected")
                locations = [loc.get('id', 'unknown') for loc in response]
                expected_locations = ['silk_board', 'kr_puram', 'whitefield', 'hebbal']
                if all(loc in locations for loc in expected_locations):
                    print(f"   ✅ All expected Bangalore locations found: {locations}")
                else:
                    print(f"   ⚠️  Location mismatch. Expected: {expected_locations}, Got: {locations}")
            elif isinstance(response, list):
                print(f"   ⚠️  Expected 4 locations, got {len(response)}")
            else:
                print(f"   ⚠️  Expected list response, got {type(response)}")
        
        return success, response

    def test_days_endpoint(self):
        """Test days endpoint"""
        success, response = self.run_test(
            "Days Endpoint",
            "GET",
            "days",
            200,
            expected_keys=["days"]
        )
        
        if success and "days" in response:
            days = response["days"]
            if len(days) == 7:
                print(f"   ✅ Found 7 days as expected: {days}")
            else:
                print(f"   ⚠️  Expected 7 days, got {len(days)}")
        
        return success, response

    def test_valid_traffic_prediction(self):
        """Test traffic prediction with valid inputs"""
        success, response = self.run_test(
            "Valid Traffic Prediction",
            "POST",
            "predict-traffic",
            200,
            data={
                "place": "silk_board",
                "day": "Monday",
                "start_hour": 8,
                "end_hour": 11
            },
            expected_keys=["place", "place_name", "predictions", "peak_hour", "insight"]
        )
        
        if success and "predictions" in response:
            predictions = response["predictions"]
            expected_hours = list(range(8, 12))  # 8, 9, 10, 11
            actual_hours = [p.get("hour") for p in predictions]
            
            if actual_hours == expected_hours:
                print(f"   ✅ Correct hour range: {actual_hours}")
            else:
                print(f"   ⚠️  Hour mismatch. Expected: {expected_hours}, Got: {actual_hours}")
            
            # Check prediction structure
            if predictions:
                pred = predictions[0]
                required_fields = ["hour", "traffic_value", "traffic_level", "color", "severity"]
                if all(field in pred for field in required_fields):
                    print(f"   ✅ Prediction structure correct")
                else:
                    print(f"   ⚠️  Missing prediction fields: {required_fields}")
        
        return success, response

    def test_invalid_location(self):
        """Test traffic prediction with invalid location"""
        return self.run_test(
            "Invalid Location Validation",
            "POST",
            "predict-traffic",
            400,
            data={
                "place": "invalid_location",
                "day": "Monday",
                "start_hour": 8,
                "end_hour": 11
            }
        )

    def test_invalid_day(self):
        """Test traffic prediction with invalid day"""
        return self.run_test(
            "Invalid Day Validation",
            "POST",
            "predict-traffic",
            400,
            data={
                "place": "silk_board",
                "day": "InvalidDay",
                "start_hour": 8,
                "end_hour": 11
            }
        )

    def test_invalid_hour_range(self):
        """Test traffic prediction with end_hour < start_hour"""
        return self.run_test(
            "Invalid Hour Range Validation",
            "POST",
            "predict-traffic",
            400,
            data={
                "place": "silk_board",
                "day": "Monday",
                "start_hour": 15,
                "end_hour": 10
            }
        )

    def test_all_locations_prediction(self):
        """Test traffic prediction for all 4 locations"""
        locations = ["silk_board", "kr_puram", "whitefield", "hebbal"]
        all_passed = True
        
        for location in locations:
            success, _ = self.run_test(
                f"Traffic Prediction - {location}",
                "POST",
                "predict-traffic",
                200,
                data={
                    "place": location,
                    "day": "Tuesday",
                    "start_hour": 9,
                    "end_hour": 12
                }
            )
            if not success:
                all_passed = False
        
        return all_passed

def main():
    print("🚦 Starting Bangalore Traffic Sentinel API Tests")
    print("=" * 60)
    
    tester = BangaloreTrafficAPITester()
    
    # Run all tests
    test_results = []
    
    # Basic endpoint tests
    test_results.append(tester.test_root_endpoint())
    test_results.append(tester.test_locations_endpoint())
    test_results.append(tester.test_days_endpoint())
    
    # Traffic prediction tests
    test_results.append(tester.test_valid_traffic_prediction())
    test_results.append(tester.test_invalid_location())
    test_results.append(tester.test_invalid_day())
    test_results.append(tester.test_invalid_hour_range())
    
    # Test all locations
    all_locations_passed = tester.test_all_locations_prediction()
    test_results.append((all_locations_passed, {}))
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n✨ Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Backend API tests mostly successful!")
        return 0
    else:
        print("⚠️  Backend API has significant issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())