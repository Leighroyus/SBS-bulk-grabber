# *** SBS Bulk Grabber v0.2 - Leigh Sullivan 2019-11-05  ***

import json
from fuzzywuzzy import fuzz
from SBS_single_tv_object_class import SBS_single_tv_object_class
import SBS_download_show

from urllib.request import urlopen

# *** constant base API URL for show list ***
API_URL_BASE = "http://www.sbs.com.au/api/video_search/v2/?filters=%7Bsection%7D%7BPrograms%7D&m=1&range="

# *** function to build web request strings ***
def create_url_list(list_size):

    loop_range = int(list_size / 50)
    list_remainder = list_size % 50
    url_list = []

    for x in range(1, loop_range):
        if x == 1:
            y = 1
            z = 50
            url_range = str(y) + "-" + str(z)
            url_list.append(API_URL_BASE + url_range)
        else:
            url_range = str(y + 1) + "-" + str(z)
            url_list.append(API_URL_BASE + url_range)

        y = 50 * x
        z = y + 50

    url_range = str(z + 1) + "-" + str(z + list_remainder)
    url_list.append(API_URL_BASE + url_range)

    return (url_list)

# *** function to build raw list of shows from json data ***
def create_raw_show_list(url_list):
    entries = []
    for url in url_list:
        # get raw data as json object
        #raw = urllib2.urlopen(url)
        raw = urlopen(url)
        # parse json object data
        json_obj = json.load(raw)
        # get "entries" which is a list
        entries = entries + json_obj["entries"]
    return entries

# *** function to build process list of tv show objects ***
def create_processed_list(raw_list):
    unknown_index = 9999
    show_list = []
    for single_entry in raw_list:
        # get values from raw list and populate tv show object
        SBS_single_tv_object = SBS_single_tv_object_class()
        SBS_single_tv_object.str_title = single_entry["title"]
        try:
            SBS_single_tv_object.num_episode = single_entry["pl1$episodeNumber"]
        except:
            pass
        SBS_single_tv_object.dtm_dateadded = single_entry["media$availableDate"]
        try:
            SBS_single_tv_object.str_index_ID = single_entry["pl1$pilatId"]
        except:
            SBS_single_tv_object.str_index_ID = str(unknown_index)
            unknown_index = unknown_index + 1
            pass
        SBS_single_tv_object.num_video_ID = single_entry["id"].split("/")[-1]
        # append tv show object to processed list
        show_list.append(SBS_single_tv_object)
    return show_list

# *** function to add group ID to list of shows using edit distance algorithm ***
def add_group_ID_to_list(sorted_list,group_match_threshold):
    l = 0
    group_ID = 1
    for show in sorted_list:
        if l < total_num_of_shows - 1:
            next_show = sorted_list[l + 1]
            show_title_substr = show.str_title[:show.str_title.find('-')]
            next_show_title_substr = next_show.str_title[:next_show.str_title.find('-')]
            lev = fuzz.ratio(show_title_substr, next_show_title_substr)

        if lev < group_match_threshold:
            group_ID = group_ID + 1

        if l < total_num_of_shows - 1:
            next_show.num_group_ID = group_ID
            sorted_list[l + 1] = next_show

        l = l + 1
    return sorted_list

# *** function to get total number of shows available ***
def get_total_number_of_shows():
    url = API_URL_BASE + "1-1"
    raw = urlopen(url)
    # parse json object data
    json_obj = json.load(raw)
    # get "entries" which is a list
    return json_obj["totalResults"]

# get total number of shows available
total_shows = get_total_number_of_shows()

# get list of urls, set here how many shows you want to return
url_list = create_url_list(total_shows)

# create raw list of json data from url list
raw_show_list = create_raw_show_list(url_list)

# store the total number of shows
total_num_of_shows = len(raw_show_list)

# process the raw list into nice tv show objects :)
SBS_show_list = create_processed_list(raw_show_list)

# sort the process list by pl1$pilatId, which appears to work well for episode ordering
SBS_sorted_list = sorted(SBS_show_list, key=lambda SBS_show_list: SBS_show_list.str_index_ID, reverse=False)

# add group ID to sorted tv show list, with levenshtein matching for grouping threshold set at 80% match
SBS_sorted_list = add_group_ID_to_list(SBS_sorted_list,80)

# print sorted list
for index, show in enumerate(SBS_sorted_list):

    print("Loop ID: " + str(index) + " Group ID: " + str(
        show.num_group_ID) + " Index ID: " + show.str_index_ID + ", Title: " + show.str_title) # + " - Levenshtein match: %" + str(lev)
    print("http://www.sbs.com.au/ondemand/video/single/" + show.num_video_ID)

# user input loop
while True:
    show_found = False
    n = input("\nEnter SBS show Group ID to download (0 to exit): ")
    try:
        if n == "0":
            break  # stops the loop
        elif int(n) > 0:

            # create list to hold shows to be downloaded
            download_list = []

            # search through list for show group ID
            for show in SBS_sorted_list:

                # if show group ID exists start downloading all shows in that group
                if int(n) == int(show.num_group_ID):
                    print("\nNice selection, downloading now...")
                    show_found = True
                    SBS_download_show.download_show(show.num_video_ID,show.str_title)

            if show_found == False:
                print("\nSorry, can't seem to find that one...")
            else:
                print("\nDone!")

    except:
        print("\nWhat the feck was that?")

print("\nGoodbye..")


