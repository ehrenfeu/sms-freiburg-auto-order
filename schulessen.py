import sys

from time import sleep

from loguru import logger as logging

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.common.exceptions import NoSuchElementException

from schulessen_credentials import USERNAME, PASSWORD


def place_new_orders(browser):
    """Check for order buttons and click the ones titled "Bestellen".

    If a button having the title "Bestellen" is found, it is clicked and the function
    returns immmediately as the DOM of the page will be changed and no further actions
    would succeed (e.g. it's not possible to click all "Bestellen" buttons in one go).

    Parameters
    ----------
    browser : WebDriver
        The current selenium WebDriver instance.

    Returns
    -------
    list(str), list(str)
        Two lists containing the 'bstdt' (Bestelldatum?) attributes of the identified
        buttons, the first one being the "Bestellung reduzieren" buttons, the second
        one being the "Bestellen" buttons.
    """
    orders_old = []
    orders_new = []

    # xpath values:
    minus = '[title="Bestellung reduzieren"]'
    plus = '[title="Bestellen"]'
    pre_sibling_2up = "../../preceding-sibling::*"

    buttons_minus = browser.find_elements(by="css selector", value=minus)
    buttons_plus = browser.find_elements(by="css selector", value=plus)

    total_buttons = len(buttons_minus) + len(buttons_plus)
    if total_buttons == 0:
        return orders_old, orders_new

    logging.info(f"Found {total_buttons} order buttons.")
    for button in buttons_minus:
        order_date = button.get_attribute("bstdt")
        try:
            menu_cell = button.find_element(by="xpath", value=pre_sibling_2up)
            menu_text = menu_cell.text
        except Exception:
            menu_text = "--- Couldn't find menu details! ---"

        logging.info(
            f"----- ⏮  ✅ Already ordered before: [{order_date}] ⏮  ✅ -----\n"
            f"{menu_text}"
        )
        orders_old.append(order_date)

    for button in buttons_plus:
        order_date = button.get_attribute("bstdt")
        try:
            menu_cell = button.find_element(by="xpath", value=pre_sibling_2up)
            menu_text = menu_cell.text
        except Exception:
            menu_text = "--- Couldn't find menu details! ---"

        logging.info(
            f"\n----- ⭐ NEW 🍽   order option: [{order_date}] -----\n"
            f"{menu_text}\n\n"
            "🧑‍🍳 Placing order 🍽  ..."
        )
        button.click()
        orders_new.append(order_date)
        sleep(2)
        logging.info("⭐ 🍽  Done ✅")
        return orders_old, orders_new

    return orders_old, orders_new


def load_menu_page(headless=True, snap=False):
    """Start a FireFox instance and log into the SMS ordering portal.

    Parameters
    ----------
    headless : bool, optional
        Start the browser in "headless" mode, by default True.
    snap : bool, optional
        Assume Firefox is installed via "snap" and set the `binary_location`
        option accordingly (otherwise starting FF on Ubuntu 22.04 may fail
        occasionally), by default False.

    Returns
    -------
    WebDriver
        The selenium FireFox WebDriver instance.
    """
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
        logging.error(f"Login failed, message: {err}")
        sys.exit(1)

    input_username.send_keys(USERNAME)
    input_password.send_keys(PASSWORD)
    button_login.click()

    logging.info("Loading menu ordering page...")
    try:
        speiseplan = browser.find_element(by="link text", value="Speiseplan")
        speiseplan.click()
    except NoSuchElementException as err:
        logging.error(f"Dashboard error, message: {err}")
        sys.exit(2)

    return browser


def click_next_week_button(browser):
    """Find the 'Next Week' button and click it.

    Parameters
    ----------
    browser : WebDriver
        The current selenium WebDriver instance.

    Returns
    -------
    bool
        True in case exactly one 'Next Week' button was found (and clicked),
        False otherwise (indicating there is no such button, or more than one).
    """
    btns_next_week = browser.find_elements(
        by="css selector", value='[alt="Eine Woche vor"]'
    )
    if len(btns_next_week) != 1:
        return False

    btns_next_week[0].click()
    return True


def setup_logging():
    """Set loguru stderr loggging level and format."""
    logging.remove()
    logging.add(sink=sys.stderr, level="DEBUG", format="{message}\n")


if __name__ == "__main__":
    setup_logging()

    browser = load_menu_page()

    sleep(2)
    old, new = place_new_orders(browser)

    while click_next_week_button(browser):
        sleep(2)
        old, new = place_new_orders(browser)

    logging.info("No 'next week' button found, end of order period reached.")
    browser.quit()
    sys.exit(0)
