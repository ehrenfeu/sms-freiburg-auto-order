import sys

from time import sleep

from loguru import logger as logging

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.common.exceptions import NoSuchElementException

from schulessen_credentials import USERNAME, PASSWORD


def place_new_orders():
    """Check for order buttons and click the ones titled "Bestellen".

    If a button having the title "Bestellen" is found, it is clicked and the function
    returns immmediately as the DOM of the page will be changed and no further actions
    would succeed (e.g. it's not possible to click all "Bestellen" buttons in one go).

    Returns
    -------
    list(str), list(str)
        Two lists containing the 'bstdt' (Bestelldatum?) attributes of the identified
        buttons, the first one being the "Bestellung reduzieren" buttons, the second
        one being the "Bestellen" buttons.
    """
    orders_old = []
    orders_new = []

    minus = '[title="Bestellung reduzieren"]'
    plus = '[title="Bestellen"]'

    buttons_minus = browser.find_elements(by="css selector", value=minus)
    buttons_plus = browser.find_elements(by="css selector", value=plus)

    total_buttons = len(buttons_minus) + len(buttons_plus)
    if total_buttons == 0:
        return orders_old, orders_new

    logging.info(f"Found {total_buttons} order buttons.")
    for button in buttons_minus:
        order_date = button.get_attribute("bstdt")
        logging.info(f"[{order_date}]: already ordered ✅")
        orders_old.append(order_date)

    for button in buttons_plus:
        order_date = button.get_attribute("bstdt")
        logging.info(f"[{order_date}]: NEW order option ⭐")
        logging.info(f"Ordering...")
        button.click()
        orders_new.append(order_date)
        sleep(2)
        return orders_old, orders_new

    return orders_old, orders_new


# logger = logging.getLogger()
# logger.setLevel(logging.INFO)


def load_menu_page(headless=True, snap=False):
    logging.info("Starting Firefox...")
    options = FirefoxOptions()
    if snap:
        options.binary_location = "/snap/firefox/current/firefox.launcher"
    if headless:
        options.add_argument("--headless")
    browser = Firefox(options=options)

    logging.info("Loading login page...")
    browser.get("https://sms-freiburg.de/")


    logging.info("Attempting to log in...")
    try:
        input_username = browser.find_element(by="id", value="ID_USERNAME")
        input_password = browser.find_element(by="id", value="ID_PASSWORD")
        button_login = browser.find_element(by="id", value="ID_LOGIN")
    except NoSuchElementException as err:
        logging.error(f"Login failed, connection error or changed layout? Message: {err}")
        sys.exit(1)

    input_username.send_keys(USERNAME)
    input_password.send_keys(PASSWORD)
    button_login.click()

    logging.info("Loading menu ordering page...")
    try:
        speiseplan = browser.find_element(by="link text", value="Speiseplan")
        speiseplan.click()
    except NoSuchElementException as err:
        logging.error(f"Dashboard error, login failed or changed layout? Message: {err}")
        sys.exit(2)

    return browser


if __name__ == "__main__":
    browser = load_menu_page()

    while True:
        sleep(2)

        old, new = place_new_orders()
        # as long as 'new' is not empty, keep ordering:
        while new:
            old, new = place_new_orders()

        if len(old) + len(new) == 0:
            logging.info("No order buttons found, end of order period reached.")
            browser.quit()
            sys.exit(0)

        week_plus = browser.find_element(by="css selector", value='[alt="Eine Woche vor"]')
        week_plus.click()
