#!/usr/bin/env python3
"""
Quick API connectivity test script
Tests if the Treasury API is accessible and returns data
"""

import requests
import json
import sys

def test_api():
    """Test basic API connectivity"""

    print("="*70)
    print("🧪 Treasury API Connectivity Test")
    print("="*70)

    base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash"

    # Test 1: Simple request without filters
    print("\n📡 Test 1: Basic API endpoint access...")
    try:
        response = requests.get(
            base_url,
            params={"page[size]": "5", "format": "json"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; TreasuryAPITest/1.0)"},
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            record_count = len(data.get('data', []))
            print(f"   ✅ SUCCESS - Retrieved {record_count} records")

            if record_count > 0:
                sample = data['data'][0]
                print(f"   Sample date: {sample.get('record_date', 'N/A')}")
                print(f"   Sample dept: {sample.get('transaction_type', 'N/A')[:50]}")
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

    # Test 2: Specific date filter (FY2024)
    print("\n📡 Test 2: Filtered request for FY2024 (Sept 30, 2024)...")
    try:
        response = requests.get(
            base_url,
            params={
                "filter": "record_date:eq:2024-09-30",
                "page[size]": "5",
                "format": "json"
            },
            headers={"User-Agent": "Mozilla/5.0 (compatible; TreasuryAPITest/1.0)"},
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            record_count = data.get('meta', {}).get('total-count', 0)
            print(f"   ✅ SUCCESS - FY2024 has {record_count} records available")
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

    # Test 3: Fiscal year 2023
    print("\n📡 Test 3: Filtered request for FY2023 (Sept 30, 2023)...")
    try:
        response = requests.get(
            base_url,
            params={
                "filter": "record_date:eq:2023-09-30",
                "page[size]": "5",
                "format": "json"
            },
            headers={"User-Agent": "Mozilla/5.0 (compatible; TreasuryAPITest/1.0)"},
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            record_count = data.get('meta', {}).get('total-count', 0)
            print(f"   ✅ SUCCESS - FY2023 has {record_count} records available")
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

    print("\n" + "="*70)
    print("✅ API Test Complete")
    print("="*70)
    print("\nIf all tests passed, the main extractor should work fine!")
    print("Run: python src/treasury_extractor.py")

    return True

if __name__ == "__main__":
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
