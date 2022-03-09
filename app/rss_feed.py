from feedgen.feed import FeedGenerator
import pickle
import configparser
import os

def create_fresh_feed(config):
    rss_link = config["RSS"]["link"] + "/flask"
    rss_description = config["RSS"]["description"]
    rss_title = config["RSS"]["title"]
    rss_self = rss_link + "/flask/static/rss/rss.xml"
    fg = FeedGenerator()
    fg.title(rss_title)
    fg.description(rss_description)
    fg.link( href=rss_link )
    fg.link( href=rss_self, rel='self' )
    fg.language('en')
    rssfeed  = fg.rss_str(pretty=True) # Get the RSS feed as string
    fg.rss_file('./static/rss/rss.xml') # Write the RSS feed to a file
    #so we can load / append later
    with open('./static/rss/feed.obj', 'wb') as f:
        pickle.dump(fg, f)

#could be made to be generic, for other rss notifications e.g. 'funded'
def add_to_rfeed(wish):
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    rss_enable = config["RSS"]["enable"]
    if int(rss_enable) == 0:
        return 
    if not os.path.isfile("./static/rss/rss.xml"):
        print("Make new wishlist")
        create_fresh_feed(config)
    '''
    wish = {
    "goal_usd":wish["goal"],
    "title": wish["title"],
    "description":wish["desc"],
    }
    '''
    rss_title = wish["title"]
    rss_description = wish["description"]
    rss_goal = wish["goal_usd"]
    rss_link = config["RSS"]["link"] + "/flask"
    #load the current feed
    with open('./static/rss/feed.obj', 'rb') as f:
        fg = pickle.load(f)

    fe = fg.add_entry()
    fe.title(f"{rss_title} ${str(rss_goal)}")
    fe.link(href=rss_link)
    #update the feed
    fg.rss_file('./static/rss/rss.xml')
    #pickle it for later
    with open('./static/rss/feed.obj', 'wb') as f:
        pickle.dump(fg, f)


