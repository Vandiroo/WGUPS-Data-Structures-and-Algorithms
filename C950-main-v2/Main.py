# Andy Ng
# Student ID: 011877683

import csv
from datetime import datetime, timedelta
import logging

# Set up logging without timestamp
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

class HashMap:
    def __init__(self, initialCapacity=40):
        self.map = [[] for _ in range(initialCapacity)]

    def insert(self, key, package):
        section = hash(key) % len(self.map)
        sectionList = self.map[section]

        for kv in sectionList:
            if kv[0] == key:
                kv[1] = package
                return True

        keyValue = [key, package]
        sectionList.append(keyValue)
        return True

    def search(self, key):
        section = hash(key) % len(self.map)
        sectionList = self.map[section]
        for pair in sectionList:
            if key == pair[0]:
                return pair[1]
        return None

    def resize(self):
        resizedMap = HashMap(initialCapacity=len(self.map) * 2)

        for section in self.map:
            for package in section:
                resizedMap.insert(package[0], package[1])

        self.map = resizedMap.map

    def remove(self, key):
        slot = hash(key) % len(self.map)
        destination = self.map[slot]

        for i, kv in enumerate(destination):
            if kv[0] == key:
                del destination[i]
                return True
        return False

class Package:
    def __init__(self, ID, address, city, state, zipcode, deadline_time, weight, status):
        self.ID = ID
        self.address = address
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.deadline_time = deadline_time
        self.weight = weight
        self.status = status
        self.departure_time = None
        self.delivery_time = None
        self.truck_number = None  # Track which truck the package is assigned to
        self.is_address_corrected = False  # Flag to track if Package 9's address is corrected
        self.arrival_time = timedelta(hours=9, minutes=5) if ID in [6, 25, 28, 32] else timedelta(hours=0)  # Delayed packages arrive at 9:05 AM

    def update_status(self, current_time):
        if self.arrival_time > current_time:
            self.status = "Delayed"
        elif self.delivery_time and self.delivery_time <= current_time:
            self.status = f"Delivered at {self.delivery_time}"
        elif self.departure_time and self.departure_time <= current_time:
            self.status = f"En route since {self.departure_time}"
        else:
            self.status = "At Hub"

    def update_address_for_package_9(self, current_time):
        """
        Update Package 9's address if the current time is 10:20 AM or later.
        """
        if self.ID == 9 and current_time >= timedelta(hours=10, minutes=20) and not self.is_address_corrected:
            self.address = "410 S. State St., Salt Lake City, UT 84111"
            self.is_address_corrected = True

class Truck:
    def __init__(self, capacity, speed, load, packages, mileage, address, depart_time):
        self.capacity = capacity
        self.speed = speed
        self.load = load
        self.packages = packages
        self.mileage = mileage
        self.address = address
        self.depart_time = depart_time
        self.time = depart_time

    def add_mileage(self, distance):
        self.mileage += distance

    def __str__(self):
        return f"{self.capacity}, {self.speed}, {self.load}, {self.packages}, {self.mileage}, {self.address}, {self.depart_time}"

def loadCSV(filename):
    """
    Load CSV data from a file.

    Args:
        filename (str): Path to the CSV file.
    Returns:
        list: A list of rows from the CSV file.
    """
    data = []
    try:
        with open(filename, encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error loading file '{filename}': {e}")
    return data

# Load distance data
CSVDistance = loadCSV("Distance.csv")

# Load address data
CSVAddress = loadCSV("Address.csv")

# Load package data
CSVPackage = loadCSV("PackageFiles.csv")

def loadPackageData(filename, packageHashTable):
    """
    Load package data into the hash table.

    Args:
        filename (str): Path to the package data CSV file.
        packageHashTable (HashMap): Instance of HashMap to store package data.
    """
    with open(filename, mode='r', encoding='utf-8-sig') as packageInfo:
        packageData = csv.reader(packageInfo)
        for package in packageData:
            pID = int(package[0])
            pAddress = package[1] if int(package[0]) != 9 else "300 State St, Salt Lake City, UT, 84103"
            pCity = package[2]
            pState = package[3]
            pZipcode = package[4]
            pDeadline_time = package[5]
            pWeight = package[6]
            pSpecialNote = package[7] if len(package) > 7 else ''
            pStatus = "At Hub"

            p = Package(pID, pAddress, pCity, pState, pZipcode, pDeadline_time, pWeight, pStatus)
            packageHashTable.insert(pID, p)

def distanceBetween(x, y):
    """
    Calculate the distance between two locations.

    Args:
        x (int): Index of the first location.
        y (int): Index of the second location.
    Returns:
        float: The distance between the two locations.
    """
    distance = CSVDistance[x][y]
    if distance == '':
        distance = CSVDistance[y][x]
    return float(distance)

def getAddress(address):
    """
    Get the address index from the address CSV.

    Args:
        address (str): The address string to find.
    Returns:
        int or None: The index of the address in the CSV, or None if not found.
    """
    for idx, row in enumerate(CSVAddress):
        if address in row[0]:  # Match the address string in the appropriate column
            return idx
    return None

def calculate_total_mileage(trucks):
    """
    Calculate the total mileage traveled by all trucks.

    Args:
        trucks (list): A list of Truck objects.
    Returns:
        float: The total mileage traveled by all trucks.
    """
    total_mileage = sum(truck.mileage for truck in trucks)
    return total_mileage

def deliverPackages(truck, packageTable, driver_availability):
    """
    Simulate the delivery of packages by the truck using a greedy algorithm.

    Args:
        truck (Truck): The Truck object.
        packageTable (HashMap): The HashMap containing package data.
        driver_availability (list): List of timedelta objects representing when each driver is available.
    """
    # Find the earliest available driver
    earliest_driver_time = min(driver_availability)
    if truck.depart_time < earliest_driver_time:
        truck.depart_time = earliest_driver_time  # Wait until a driver is available

    # Assign the truck to the earliest available driver
    driver_index = driver_availability.index(earliest_driver_time)
    driver_availability[driver_index] = truck.depart_time  # Driver is now occupied

    current_location = truck.address
    while truck.packages:
        min_distance = float('inf')
        next_package_id = None
        next_package_address = None
        for packageID in truck.packages:
            package = packageTable.search(packageID)
            if package:
                delivery_address = package.address
                current_address_index = getAddress(current_location)
                delivery_address_index = getAddress(delivery_address)
                if current_address_index is not None and delivery_address_index is not None:
                    distance = distanceBetween(current_address_index, delivery_address_index)
                    if distance < min_distance:
                        min_distance = distance
                        next_package_id = packageID
                        next_package_address = delivery_address
                else:
                    logging.warning(f"Address '{delivery_address}' not found in the CSV. Skipping this package.")
                    truck.packages.remove(packageID)
        if next_package_id is not None:
            truck.add_mileage(min_distance)
            truck.time += timedelta(hours=min_distance / truck.speed)
            package = packageTable.search(next_package_id)
            if package:
                package.delivery_time = truck.time
                package.update_status(truck.time)
                current_location = next_package_address
                truck.packages.remove(next_package_id)

    # Update driver availability when the truck returns
    driver_availability[driver_index] = truck.time

def updatePackageAddress(packageTable, packageID, new_address, current_time, correction_time):
    if current_time >= correction_time:
        package = packageTable.search(packageID)
        if package:
            package.address = new_address
            logging.info(f"Address for package {packageID} updated to: {new_address}")

def capturePackageStatus(truck, packageTable, captureTimes):
    """
    Capture the status of packages at specific times.

    Args:
        truck (Truck): The Truck object.
        packageTable (HashMap): The HashMap containing package data.
        captureTimes (list): List of times to capture package statuses.
    Returns:
        dict: A dictionary containing package statuses at the specified times.
    """
    statusSnapshots = {captureTime: [] for captureTime in captureTimes}
    for packageID in range(1, 41):
        package = packageTable.search(packageID)
        if package:
            for captureTime in captureTimes:
                # Handle Package 9's address correction based on the capture time
                if package.ID == 9:
                    if captureTime < timedelta(hours=10, minutes=20):
                        # Display the incorrect address for Package 9 before 10:20 AM
                        package.address = "300 State St., Salt Lake City, UT, 84103"
                    else:
                        # Display the corrected address for Package 9 at or after 10:20 AM
                        package.address = "410 S. State St., Salt Lake City, UT 84111"

                # Update the package status based on the capture time
                package.update_status(captureTime)

                # Find the truck the package is assigned to
                truck_no = package.truck_number  # Use the truck_number attribute

                # Capture the package status
                status = (captureTime, packageID, package.status, package.address, truck_no)
                statusSnapshots[captureTime].append(status)
    return statusSnapshots

def displayStatusSnapshots(statusSnapshots):
    """
    Display the captured package statuses.

    Args:
        statusSnapshots (dict): Dictionary of captured package statuses.
    """
    for captureTime, statuses in statusSnapshots.items():
        logging.info(f"Time: {captureTime}")
        for status in statuses:
            captureTime, packageID, package_status, package_address, truck_no = status
            logging.info(f"Package ID: {packageID}, Address: {package_address}, "
                         f"Deadline: {packageTable.search(packageID).deadline_time}, Truck No: {truck_no}, "
                         f"Delivery Time: {packageTable.search(packageID).delivery_time}, Status: {package_status}")

def get_user_input_time():
    """
    Prompt the user to input a specific time.

    Returns:
        datetime.timedelta: The input time as a timedelta object.
    """
    input_time_str = input("Enter the time (HH:MM): ")
    try:
        hours, minutes = map(int, input_time_str.split(':'))
        return timedelta(hours=hours, minutes=minutes)
    except ValueError:
        logging.error("Invalid time format. Please use HH:MM format.")
        return None

def display_package_status_at_time(packageTable, trucks, input_time):
    """
    Display the status of all packages at a specific input time.

    Args:
        packageTable (HashMap): The HashMap containing package data.
        trucks (list): A list of Truck objects.
        input_time (timedelta): The input time to check the package statuses.
    """
    logging.info(f"Package statuses at {input_time}:")
    for packageID in range(1, 41):  # Assuming package IDs are from 1 to 40
        package = packageTable.search(packageID)
        if package:
            # Handle Package 9's address correction based on the input time
            if package.ID == 9:
                if input_time < timedelta(hours=10, minutes=20):
                    # Display the incorrect address for Package 9 before 10:20 AM
                    package.address = "300 State St, Salt Lake City, UT, 84103"
                else:
                    # Display the corrected address for Package 9 at or after 10:20 AM
                    package.address = "410 S. State St., Salt Lake City, UT 84111"

            # Update the package status based on the input time
            package.update_status(input_time)

            # Find the truck the package is assigned to
            truck_no = package.truck_number  # Use the truck_number attribute

            # Display the package information
            logging.info(f"Package ID: {packageID}, Address: {package.address}, "
                         f"Deadline: {package.deadline_time}, Truck No: {truck_no}, "
                         f"Delivery Time: {package.delivery_time}, Status: {package.status}")

# Assign packages to trucks based on constraints
def assign_packages_to_trucks(packageTable, truck1, truck2, truck3):
    # Packages that must be on Truck 2
    truck2_only_packages = [3, 18, 36, 38]
    for package_id in truck2_only_packages:
        package = packageTable.search(package_id)
        if package:
            truck2.packages.append(package_id)
            package.truck_number = 2

    # Packages delayed until 9:05 AM (assigned to Truck 3)
    delayed_packages = [6, 25, 28, 32]
    for package_id in delayed_packages:
        package = packageTable.search(package_id)
        if package:
            truck3.packages.append(package_id)
            package.truck_number = 3

    # Packages that must be delivered together
    group1 = [14, 15, 19]
    group2 = [16, 13, 19]
    group3 = [20, 13, 15]

    # Assign group1 to Truck 1
    for package_id in group1:
        package = packageTable.search(package_id)
        if package:
            truck1.packages.append(package_id)
            package.truck_number = 1

    # Assign group2 to Truck 1
    for package_id in group2:
        package = packageTable.search(package_id)
        if package:
            truck1.packages.append(package_id)
            package.truck_number = 1

    # Assign group3 to Truck 1
    for package_id in group3:
        package = packageTable.search(package_id)
        if package:
            truck1.packages.append(package_id)
            package.truck_number = 1

    # Assign remaining packages to Truck 1 or Truck 2
    for package_id in range(1, 41):
        if package_id not in truck1.packages and package_id not in truck2.packages and package_id not in truck3.packages:
            package = packageTable.search(package_id)
            if package:
                if package_id not in delayed_packages:
                    if len(truck1.packages) < 16:
                        truck1.packages.append(package_id)
                        package.truck_number = 1
                    else:
                        truck2.packages.append(package_id)
                        package.truck_number = 2

    # Ensure Truck 3 does not leave before 9:05 AM
    truck3.depart_time = timedelta(hours=9, minutes=5)

if __name__ == "__main__":
    # Create Truck objects representing the three delivery trucks
    truck1 = Truck(16, 18, None, [], 0.0, "4001 South 700 East", timedelta(hours=8))
    truck2 = Truck(16, 18, None, [], 0.0, "4001 South 700 East", timedelta(hours=8))
    truck3 = Truck(16, 18, None, [], 0.0, "4001 South 700 East", timedelta(hours=9, minutes=5))

    # Create an instance of the HashMap to store all package data
    packageTable = HashMap()

    # Load the package data into the hash table
    loadPackageData("PackageFiles.csv", packageTable)

    # Assign packages to trucks based on constraints
    assign_packages_to_trucks(packageTable, truck1, truck2, truck3)

    # Track driver availability
    driver_availability = [timedelta(hours=8), timedelta(hours=8)]  # Both drivers start at 8:00 AM

    # Simulate package delivery for each truck
    correction_time = timedelta(hours=10, minutes=20)
    corrected_address = "410 S. State St., Salt Lake City, UT 84111"

    trucks = [truck1, truck2, truck3]
    for truck in trucks:
        deliverPackages(truck, packageTable, driver_availability)
        updatePackageAddress(packageTable, 9, corrected_address, truck.time, correction_time)

    # Calculate and display total mileage
    total_mileage = calculate_total_mileage(trucks)
    logging.info(f"Total Mileage Traveled by All Trucks: {total_mileage} miles")

    # Define the times to capture package statuses
    captureTimes = [timedelta(hours=8, minutes=35), timedelta(hours=9, minutes=25),
                    timedelta(hours=9, minutes=35), timedelta(hours=10, minutes=25),
                    timedelta(hours=12, minutes=3), timedelta(hours=13, minutes=12)]

    # Capture package statuses for each truck
    truck1StatusSnapshots = capturePackageStatus(truck1, packageTable, captureTimes)
    truck2StatusSnapshots = capturePackageStatus(truck2, packageTable, captureTimes)
    truck3StatusSnapshots = capturePackageStatus(truck3, packageTable, captureTimes)

    # Display status snapshots for each truck
    logging.info("Truck 1 Status Snapshots:")
    displayStatusSnapshots(truck1StatusSnapshots)

    logging.info("Truck 2 Status Snapshots:")
    displayStatusSnapshots(truck2StatusSnapshots)

    logging.info("Truck 3 Status Snapshots:")
    displayStatusSnapshots(truck3StatusSnapshots)

    # Get user input time
    input_time = get_user_input_time()

    # Display package statuses at the user-specified time if input time is valid
    if input_time:
        display_package_status_at_time(packageTable, trucks, input_time)