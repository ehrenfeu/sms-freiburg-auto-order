import sys

from time import sleep

from loguru import logger as logging

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.common.exceptions import NoSuchElementException

from schulessen_credentials import USERNAME, PASSWORD


def menu_details(order_button):
    """Try to find the menu details related to a given order button.

    Parameters
    ----------
    order_button : selenium.webdriver.remote.webelement.WebElement
        An order (or order cancellation) button.

    Returns
    -------
    str
        The menu details. If the identified text has a well-known format (i.e.
        consisting of three sections separated by double-newlines), it is parsed
        and re-formatted to only contain the main dish description in a single
        line (dropping the last one which usually contains allergene details).
    """
    # xpath values:
    pre_sibling_2up = "../../preceding-sibling::*"
    try:
        menu_cell = order_button.find_element(by="xpath", value=pre_sibling_2up)
        menu_text = menu_cell.text
    except Exception:
        msg = "--- Couldn't find menu details! ---"
        logging.warning(msg)
        return msg

    # a "regular" menu text contains three sections which are separated by two
    # consecutive newlines - if that's the case, only return the middle one
    # (containing the main dish) replacing single newlines by a space:
    menu_sections = menu_text.split("\n\n")
    if len(menu_sections) != 3:
        logging.warning("Couldn't parse menu details!")
        return menu_text

    main_dish = menu_sections[1].split("\n")
    return " ".join(main_dish[:-1])


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

    buttons_minus = browser.find_elements(by="css selector", value=minus)
    buttons_plus = browser.find_elements(by="css selector", value=plus)

    total_buttons = len(buttons_minus) + len(buttons_plus)
    if total_buttons == 0:
        return orders_old, orders_new

    logging.info(f"Found {total_buttons} order buttons.")
    for button in buttons_minus:
        order_date = button.get_attribute("bstdt")
        menu_text = menu_details(button)
        print(f"--- ⏮  ✅ Ordered already: [{order_date}] ---\n{menu_text}\n")
        orders_old.append(order_date)

    for button in buttons_plus:
        order_date = button.get_attribute("bstdt")
        menu_text = menu_details(button)
        print(f"\n--- ⭐ NEW 🍽   order option: [{order_date}] ---\n{menu_text}\n\n")
        print("🧑‍🍳 Placing order 🍽 ...")
        button.click()
        orders_new.append(order_date)
        sleep(2)
        print("⭐ 🍽  Done ✅\n")
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

    print("====== Navigating to next week... ======\n")
    btns_next_week[0].click()
    return True


def setup_logging(level="WARNING"):
    """Set loguru stderr loggging level."""
    logging.remove()
    logging.add(sink=sys.stderr, level=level)


def print_orders(old, new):
    """Print a summary of existing and new orders.

    Parameters
    ----------
    old : list(dict)
        A list with existing order details, as returned by `place_new_orders()`.
    new : list(dict)
        Same as `old`, only for newly placed orders.
    """
    if not old and not new:
        return

    ymd = "%Y-%m-%d"
    dt_min = min([x["date"] for x in old + new]).strftime(ymd)
    dt_max = max([x["date"] for x in old + new]).strftime(ymd)

    print(f"------ Summary 📋 for [{dt_min}] to [{dt_max}] 📅 ------")
    if old:
        print("\n--- ⏮  ✅ Existing orders:")
        for order in old:
            print(f"> [{order['date'].strftime(ymd)}] - {order['menu']}")

    if new:
        print("\n--- 🆕 NEWLY 🍽  placed orders:")
        for order in new:
            print(f"> 🧑‍🍳 ⭐ [{order['date'].strftime(ymd)}] - {order['menu']}")


if __name__ == "__main__":
    setup_logging()

    browser = load_menu_page()

    sleep(2)
    old, new = place_new_orders(browser)

    while click_next_week_button(browser):
        sleep(2)
        old, new = place_new_orders(browser)

    print("No more 'next week' button found, end of order period reached.")

    browser.quit()
