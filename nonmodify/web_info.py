"""Handles webscraping functionality"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

from nonmodify.class_info import class_info as ci


def access_class(driver, subject, number):
    """clear search bars and search the class input
    Args:
        driver: Selenium webdriver
        subject: str (eg. ENG, MAT, IEE, etc.)
        number: str (123, 101, 534, etc.)
    """
    try:
        # Add a short wait
        time.sleep(1)

        input_number_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "catalogNbr"))
        )
        input_number_element.clear()
        input_number_element.send_keys("102")

        # Wait for and interact with the subject input
        input_class_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[name='subject'][placeholder='Subject']")
            )
        )
        input_class_element.clear()
        input_class_element.send_keys("ENG")

        # Add a short wait
        time.sleep(1)

        # Wait for the search button to be clickable
        search_button_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "search-button"))
        )
        search_button_element.click()
    except Exception as e:
        print(f"An error occurred: {e}")


def scan_boxes(driver):
    """Look through the page and scan through divs
    Args:
        driver: Selenium Webdriver
    Returns:
        str: formatted output text for aggregation function for one class
    """
    try:
        # Wait for the class results to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "class-results"))
        )

        print("class results loaded detected")

        # Find the container with class information
        class_results = driver.find_element(By.ID, "class-results")

        # Find all class rows
        class_rows = class_results.find_elements(By.CLASS_NAME, "class-accordion")

        output_text = ""

        for row in class_rows:
            # Extract relevant information
            course_info = row.find_element(By.CLASS_NAME, "course").text
            number = row.find_element(By.CLASS_NAME, "number").text
            instructor = row.find_element(By.CLASS_NAME, "instructor").text
            days = row.find_element(By.CLASS_NAME, "days").text
            time_start = row.find_element(By.CLASS_NAME, "start").text
            time_end = row.find_element(By.CLASS_NAME, "end").text
            location = row.find_element(By.CLASS_NAME, "location").text
            seats = row.find_element(By.CLASS_NAME, "seats").text

            # Format the output
            output_text += f"{course_info}\n"
            output_text += f"{number}\n"
            output_text += f"{instructor}\n"
            output_text += f"{days} | {time_start} - {time_end}\n"
            output_text += f"{location}\n"
            output_text += f"{seats}\n"
            output_text += "\n"  # Add a blank line between classes

        return output_text

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def next_page(driver, timeout=10):
    """Next Page toggler, this function seems to work better than the first
    Args:
        driver: Selenium Driver
        timeout: int - timeout in seconds. Default is 10
    Returns:
        bool: status if next page was successfully toggled
    """
    try:
        # Wait for the "Next" button to be present
        next_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[contains(@class, 'page-item')]/a[text()='Next']")
            )
        )

        # Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)

        # Wait for a short time to allow any animations to complete
        driver.implicitly_wait(2)

        # Click the "Next" button
        next_button.click()
        print("Clicked 'Next' button successfully")
        return True
    except ElementClickInterceptedException:
        print("Click was intercepted. Attempting to click with JavaScript.")
        driver.execute_script("arguments[0].click();", next_button)
        return True
    except Exception as e:
        print(f"Failed to find or click 'Next' button: {str(e)}")
        return False


def wait_for_page_load(driver, timeout=10):
    """Waits for page to load; use in if statement implementation
    Args:
        driver: Selenium Driver
        timeout: int: time before timeout in seconds.  Default is 10
    Returns:
        bool: Status of page load
    """
    try:
        # Wait for the class results container to be present
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "class-results"))
        )

        # Wait for at least one class result to be visible
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "class-accordion"))
        )

        print("Page fully loaded!")
        return True

    except TimeoutException:
        print(f"Page did not load completely within {timeout} seconds")
        return False


def all_elements(driver, timeout=10, file_name="webpage_elements.txt"):
    """scans all elements on the page and moves them to a file in format
    Args:
        driver: Selenium Driver
        timeout: int - timeout in seconds. Default is 10
        file_name: str - name of file to save to. Default is webpage_elements.txt
    """
    try:
        if wait_for_page_load(driver, timeout):

            # Find all elements on the page
            all_elements = driver.find_elements(By.XPATH, "//*")

            with open(file_name, "w", encoding="utf-8") as file:
                file.write(f"Total elements found: {len(all_elements)}\n\n")

                for index, element in enumerate(all_elements, start=1):
                    try:
                        tag_name = element.tag_name
                        element_id = element.get_attribute("id") or "N/A"
                        element_class = element.get_attribute("class") or "N/A"
                        element_text = element.text.replace("\n", " ")[
                            :50
                        ]  # Truncate long text

                        file.write(f"Element {index}:\n")
                        file.write(f"  Tag: {tag_name}\n")
                        file.write(f"  ID: {element_id}\n")
                        file.write(f"  Class: {element_class}\n")
                        file.write(f"  Text: {element_text}\n")
                        file.write("\n")
                    except StaleElementReferenceException:
                        file.write(f"Element {index}: Stale element, skipping\n\n")
                    except Exception as e:
                        file.write(f"Error processing element {index}: {str(e)}\n\n")

            print(f"Results have been saved to {file_name}")
        else:
            print("Page did not load properly")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def scan_class(class_name: ci, driver):
    access_class(driver, class_name.subj, class_name.nbr)
