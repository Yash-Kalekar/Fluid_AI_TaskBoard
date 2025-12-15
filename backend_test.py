#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class TaskBoardAPITester:
    def __init__(self, base_url="https://simpleboard-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (expected {expected_status})"
                if response.text:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"raw_response": response.text}
            
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_list_tasks_empty(self):
        """Test listing tasks when empty"""
        success, data = self.run_test("List Tasks (Empty)", "GET", "tasks", 200)
        if success and isinstance(data, list):
            self.log_test("List Tasks Returns Array", True, f"Got {len(data)} tasks")
            return True, data
        elif success:
            self.log_test("List Tasks Returns Array", False, f"Expected array, got {type(data)}")
        return success, data

    def test_create_task_valid(self, title: str = "Test Task"):
        """Test creating a valid task"""
        success, data = self.run_test(
            f"Create Task: '{title}'", 
            "POST", 
            "tasks", 
            201, 
            {"title": title}
        )
        
        if success and "task" in data:
            task = data["task"]
            if task.get("title") == title and "id" in task:
                self.log_test("Create Task Response Valid", True, f"Task ID: {task['id']}")
                return True, task
            else:
                self.log_test("Create Task Response Valid", False, f"Invalid task data: {task}")
        
        return success, data

    def test_create_task_invalid_short_title(self):
        """Test creating task with short title (should fail with 422)"""
        return self.run_test(
            "Create Task (Short Title)", 
            "POST", 
            "tasks", 
            422, 
            {"title": "ab"}  # Only 2 characters
        )

    def test_patch_task_completion(self, task_id: str, completed: bool = True):
        """Test toggling task completion"""
        action = "Complete" if completed else "Uncomplete"
        success, data = self.run_test(
            f"{action} Task", 
            "PATCH", 
            f"tasks/{task_id}", 
            200, 
            {"completed": completed}
        )
        
        if success and "task" in data:
            task = data["task"]
            if task.get("completed") == completed:
                self.log_test(f"Task {action} Status Updated", True, f"Completed: {task['completed']}")
                return True, task
            else:
                self.log_test(f"Task {action} Status Updated", False, f"Expected completed={completed}, got {task.get('completed')}")
        
        return success, data

    def test_patch_nonexistent_task(self):
        """Test patching non-existent task (should return 404)"""
        return self.run_test(
            "Patch Non-existent Task", 
            "PATCH", 
            "tasks/nonexistent-id", 
            404, 
            {"completed": True}
        )

    def test_delete_task(self, task_id: str):
        """Test deleting a task"""
        return self.run_test(
            "Delete Task", 
            "DELETE", 
            f"tasks/{task_id}", 
            204
        )

    def test_delete_nonexistent_task(self):
        """Test deleting non-existent task (should return 404)"""
        return self.run_test(
            "Delete Non-existent Task", 
            "DELETE", 
            "tasks/nonexistent-id", 
            404
        )

    def test_persistence(self):
        """Test that tasks persist by creating, listing, and verifying"""
        print("\n🔍 Testing Persistence...")
        
        # Create a unique task
        test_title = f"Persistence Test {datetime.now().strftime('%H%M%S')}"
        success, task_data = self.test_create_task_valid(test_title)
        
        if not success:
            return False
        
        task_id = task_data.get("id")
        if not task_id:
            self.log_test("Persistence Test", False, "No task ID returned")
            return False
        
        # List tasks and verify our task exists
        success, tasks_list = self.test_list_tasks_empty()
        if not success:
            return False
        
        # Find our task in the list
        found_task = None
        for task in tasks_list:
            if task.get("id") == task_id:
                found_task = task
                break
        
        if found_task and found_task.get("title") == test_title:
            self.log_test("Task Persistence Verified", True, f"Found task with ID {task_id}")
            return True
        else:
            self.log_test("Task Persistence Verified", False, f"Task {task_id} not found in list")
            return False

    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting Task Board API Test Suite")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)

        # Basic connectivity
        self.test_health_check()
        
        # Initial state
        self.test_list_tasks_empty()
        
        # Task creation
        success, task1 = self.test_create_task_valid("First Test Task")
        task1_id = task1.get("id") if success else None
        
        success, task2 = self.test_create_task_valid("Second Test Task")
        task2_id = task2.get("id") if success else None
        
        # Validation
        self.test_create_task_invalid_short_title()
        
        # Task operations (if we have valid tasks)
        if task1_id:
            self.test_patch_task_completion(task1_id, True)
            self.test_patch_task_completion(task1_id, False)
        
        if task2_id:
            self.test_delete_task(task2_id)
        
        # Error cases
        self.test_patch_nonexistent_task()
        self.test_delete_nonexistent_task()
        
        # Persistence
        self.test_persistence()
        
        # Final summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = TaskBoardAPITester()
    return tester.run_full_test_suite()

if __name__ == "__main__":
    sys.exit(main())