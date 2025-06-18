import requests
import random

BASE_URL = ""
LOGIN_URL = f"{BASE_URL}/users/login"
POINTS_STATUS_URL = f"{BASE_URL}/preop_bone_positioning/get_points_status"
REGISTER_POINT_URL = f"{BASE_URL}/preop_bone_positioning/register_point"
USERNAME = ""
PASSWORD = ""
OPERATION_PLAN_ID = 

def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(LOGIN_URL, json=payload)
    response.raise_for_status()
    token = response.json()["access_token"]
    return token

def get_model_points(token, i_operation_plan):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(POINTS_STATUS_URL, headers=headers, params={"i_operation_plan": i_operation_plan})
    response.raise_for_status()
    return response.json()

def register_point(token, i_operation_plan, index, coords):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "i_operation_plan": i_operation_plan,
        "index": index,
        "world_coords": {
            "x": coords[0],
            "y": coords[1],
            "z": coords[2]
        }
    }
    response = requests.post(REGISTER_POINT_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    try:
        print("Logging in...")
        token = login(USERNAME, PASSWORD)
        print("Token received.")

        print(f"Getting points for operation plan {OPERATION_PLAN_ID}...")
        points = get_model_points(token, OPERATION_PLAN_ID)
        print(f"Received {len(points)} points.")
        value = random.uniform(0, 3)

        for point in points:
            index = point["index"]
            coords = [round(c, 3) + 10 + value for c in point["model_coords"]]
            print(f"Registering point {index} with coords {coords}...")
            register_point(token, OPERATION_PLAN_ID, index, coords)
            print(f"Point {index} registered.")
            
        print("All points registered successfully.")

    except requests.HTTPError as e:
        print("HTTP Error:", e.response.status_code, e.response.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    main()
