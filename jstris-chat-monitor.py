from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from win10toast import ToastNotifier
from time import sleep, localtime
import random

#disable destruction of notification
class IndestructibleToast(ToastNotifier):
    def on_destroy(self, one, two, three, four):
        pass

#focus canvas to avoid spectate
def click_game(driver):
    canvas = driver.find_element_by_id("main")
    canvas.click()

#click lobby button
def click_lobby(driver):
    lobby_button = driver.find_element_by_id("lobby")
    lobby_button.click()
    sleep(5)

#check if in default room
def is_in_default_room(driver):
    try:
        current_room = driver.find_element_by_xpath("//tr[@class='lobbyRow myRoom']")
        current_room.find_element_by_xpath(".//td[text()='Default Room']")
        return True
    except NoSuchElementException:
        return False


#select default room from lobby menu
def click_default_room(driver):
    default_room_button = driver.find_element_by_xpath("//*[text()='Default Room']")
    default_room_button.click()

#prevent inactivity   
def make_move(driver):
    body = driver.find_element_by_tag_name("body")
    move_set = [Keys.LEFT, Keys.RIGHT, Keys.UP, "c"]
    for _ in range(6):
        body.send_keys(random.choice(move_set))
        
#play or spectate
def chat_command(driver, command):
    chat_input = driver.find_element_by_id("chatInput")
    chat_input.send_keys('/'+command, Keys.RETURN)

def play():
    chat_command(driver, "play")
    
def spec():
    chat_command(driver, "spec")

#for filtering comments sent by users rather than server
def is_user_comment(comment):
    split_comment = comment.text.strip().split()
    return split_comment[0] not in ["Watching:", "WARNING:"] and split_comment[0][-1] == ':'

def military_time():
    current_time = localtime()
    hours, minutes = current_time[3], current_time[4]
    return f"[{hours:02}:{minutes:02}]"


#check for new comments and print them, ignore seen and server messages
def print_new_comments(comments_box, comments_set):
    comments = comments_box.find_elements_by_class_name("chl")
    for comment in comments:
        if comment not in comments_set and is_user_comment(comment):
                print(f"{military_time()} {comment.text}")
                comments_set.add(comment)
       
#when users of note are online, notify
def scan_users(game_slots, seen, notifier):
    friends = {"{friends}"}
    
    all_users = game_slots.find_elements_by_tag_name("span")
    for user in all_users:
        if user.text not in seen and user.text in friends:
            notifier.show_toast(title="Jstris", msg=f"{user.text} is playing!")
            seen.add(user.text)

#navigate to site and enter default room
def setup(driver):
    driver.get("https://jstris.jezevec10.com/")
    sleep(10)
    try:
        click_lobby(driver)
        if is_in_default_room(driver):
            click_lobby(driver)
        else:
            click_default_room(driver)
        sleep(3)
        click_game(driver)
        play()
    #if server is down or there is a popup in the way, wait 2min and try again
    except (NoSuchElementException, ElementClickInterceptedException):
        print("setup failed, retrying")
        sleep(120)
        setup(driver)
    return driver.find_element_by_id("ch1"), driver.find_element_by_id("gameSlots")



if __name__ == "__main__":
    driver = webdriver.Firefox()

    comments_box, game_slots = setup(driver)

    seen_users = set()
    comments_set = set()
    seconds = 0
    notifier = IndestructibleToast()
    new_day = False

    print(f"{military_time()} Started!")
    while True:
        current_time = localtime()
        # if day changes, log new date
        if current_time[3] + current_time[4] == 0 and not new_day:
            print(f"**********{current_time[1]}/{current_time[2]}**********")
            new_day = True
        elif current_time[3] + current_time[4] != 0 and new_day:
            new_day = False
        # monitor chat, log comments
        # keep inputting moves to prevent disconnect
        try:
            if seconds == 10000:
                seen_users = set()
                seconds = 0
            print_new_comments(comments_box, comments_set)
            scan_users(game_slots, seen_users, notifier)
            play()
            click_game(driver)
            make_move(driver)
            seconds += 1
            sleep(1)
        #DOM randomly changes
        except StaleElementReferenceException:
            print(f"{military_time()} stale element encountered, running setup")
            comments_box, game_slots = setup(driver)
            print(f"{military_time()} Restarted!")
