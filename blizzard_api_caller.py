import requests
import configparser
import json
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer
import httplib2
import datetime


f_config = 'config.ini'
config = configparser.ConfigParser()
config.read(f_config)
blizzard_key = config.get('KEYS', 'blizzard')
blizzard_secret = config.get('KEYS', 'blizzard_secret')

def unpack_json(txt):
    unpacked = json.loads(txt)
    return unpacked

def get_access_token (blizzard_key, blizzard_secret):
    r = requests.post('https://us.battle.net/oauth/token', data={'grant_type': 'client_credentials'},
                  auth=(blizzard_key, blizzard_secret))
    unpacked = unpack_json(r.text)
    access_token = unpacked['access_token']
    return access_token


# Get achievement Data
locale = 'en_US'
namespace = 'static-us'
access_token = get_access_token(blizzard_key, blizzard_secret)

def get_wow_achievements_category(namespace, locale):
    directory = 'data/wow/achievement-category/index'
    url = 'https://us.api.blizzard.com/'+ directory +'?namespace='+ namespace + \
      '&locale=' + locale + '&access_token='+ access_token
    r = requests.get (url)
    unpacked = unpack_json (r.text)
    df = pd.DataFrame()
    for keys, values in unpacked.items():
        tmp = pd.DataFrame()
        for category in values:
            if isinstance(category, dict):
                for keys, values in category.items():
                    tmp[keys] = values
                df = df.append(tmp)
    return df


def get_wow_achievement_category(achievement_id, namespace, locale):
    directory = 'data/wow/achievement/'
    url = 'https://us.api.blizzard.com/' + directory + str(achievement_id) +'?namespace=' + namespace + \
          '&locale=' + locale + '&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    achievement_category = unpacked['category']
    return achievement_category['name'], unpacked['points']


def get_wow_achievement_list (namespace, locale):
    directory = 'data/wow/achievement/index'
    url = 'https://us.api.blizzard.com/'+ directory +'?namespace='+ namespace + \
      '&locale=' + locale + '&access_token='+ access_token
    r = requests.get (url)
    unpacked = unpack_json (r.text)
    df = pd.DataFrame()
    for i, achievement in enumerate(unpacked['achievements']):
        category, points = get_wow_achievement_category(achievement['id'], namespace, locale)
        row = dict(name = achievement['name'], id = achievement['id'], category = category, points = points)
        df = df.append(row, ignore_index = True)
        print(df.loc[i])
    return df


def get_wow_realms_list (namespace, locale):
    directory = 'data/wow/realm/index'
    url = 'https://us.api.blizzard.com/' + directory + '?namespace=' + namespace + \
          '&locale=' + locale + '&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    realm_names = []
    realm_ids = []
    realm_slugs = []
    for realm in unpacked ['realms']:
        realm_names.append(realm['name'])
        realm_ids.append(realm['id'])
        realm_slugs.append(realm['slug'])
    return realm_names, realm_ids, realm_slugs


#def get_wow_guild_rosters(f_in):
    #df = pd.read_csv(f_in)
    #columns = df.columns
    #guild_list = df.name
    #for i,guild in enumerate(guild_list):
       # realm = df.realm[i]
       # http = httplib2.Http()
       # status, response = http.request('https://worldofwarcraft.com/en-us/character/us/'+ guild  +'/roster')
       # try:
       #     for link in BeautifulSoup(response, parse_only=SoupStrainer('a')):
        #        if link.has_attr('href="https://worldofwarcraft.com/en-us/character/'+realm):


    #return guild_list


def get_mythic_dungeon_leaderboard_instances (realm_id, namespace, locale, access_token):
    """Returns an index of Mythic Keystone Leaderboard dungeon instances for a connected realm"""
    directory = 'data/wow/connected-realm/' + str(realm_id) + '/mythic-leaderboard/index'
    url = 'https://us.api.blizzard.com/' + directory + '?namespace=' + namespace + \
          '&locale=' + locale + '&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    current_leaderboards = unpacked['current_leaderboards']
    df = pd.DataFrame()
    for leaderboard in current_leaderboards:
        df = df.append(leaderboard, ignore_index=True)
    return df


def get_mythic_keystone_dungeon_leaderboard(realm_id,namespace,locale, instance, period):
    directory = 'data/wow/connected-realm/'
    url = 'https://us.api.blizzard.com/' + directory + str(realm_id) + '/mythic-leaderboard/' + str(instance) + \
          '/period/' + str(period) + '?namespace=' + namespace + \
          '&locale=' + locale + '&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    features = ['period', 'period_start_timestamp', 'period_end_timestamp', 'map_challenge_mode_id',
               'map_challenge_mode_name', 'map_name', 'map_id', 'connected_realm', 'keystone_affix_names',
               'keystone_affix_ids', 'keystone_affix_starting_level', 'leading_groups_ranking',
               'leading_groups_duration', 'leading_groups_completed_timestamp', 'leading_groups_keystone_level',
               'member_name, member_id', 'member_realm_id', 'member_realm_slug', 'member_faction',
               'member_specialization']
    df = pd.DataFrame()
    values = list(unpacked.values())
    map = values[1]
    period = values[2]
    period_start_timestamp  = values[3]
    period_end_timestamp  = values[4]
    map_challenge_mode_id  = values[8]
    map_challenge_mode_name = values[9]
    map_name = map['name']
    map_id = map['id']

    connected_realm = values[5]
    connected_realm = connected_realm['href']

    keystone_affixes = values[7]
    keystone_affix_names = []
    keystone_affix_ids = []
    keystone_affix_starting_level = []
    for affix in keystone_affixes:
        keystone_affix_names.append(affix['keystone_affix']['name'])
        keystone_affix_ids.append(affix['keystone_affix']['id'])
        keystone_affix_starting_level.append(affix['starting_level'])

    leading_groups = values[6]
    for leading_group in leading_groups:
        leading_groups_ranking = leading_group['ranking']
        leading_groups_duration = leading_group['duration']
        leading_groups_completed_timestamp = leading_group['completed_timestamp']
        leading_groups_keystone_level = leading_group['keystone_level']
        members = leading_group['members']
        for member in members:
            member_name = member['profile']['name']
            member_id = member['profile']['id']
            member_realm_id = member['profile']['realm']['id']
            member_realm_slug =  member['profile']['realm']['slug']
            member_faction = member['faction']['type']
            member_specialization = member['specialization']['id']
            tmp = {'period':period,
                    'period_start_timestamp':period_start_timestamp,
                   'period_end_timestamp':period_end_timestamp,
                   'map_challenge_mode_id':map_challenge_mode_id,
                   'map_challenge_mode_name':map_challenge_mode_name,
                   'map_name':map_name,
                   'map_id':map_id,
                   'connected_realm':connected_realm,
                   'keystone_affix_names':keystone_affix_names,
                   'keystone_affix_ids':keystone_affix_ids,
                   'keystone_affix_starting_level':keystone_affix_starting_level,
                   'leading_groups_ranking':leading_groups_ranking,
                   'leading_groups_duration':leading_groups_duration,
                   'leading_groups_completed_timestamp':leading_groups_completed_timestamp,
                   'leading_groups_keystone_level':leading_groups_keystone_level,
                   'member_name':member_name,
                   'member_id':member_id,
                   'member_realm_id':member_realm_id,
                   'member_realm_slug':member_realm_slug,
                   'member_faction':member_faction,
                   'member_specialization':member_specialization}
        df = df.append(tmp, ignore_index=True)
    return (df)


def get_starcraft_achievements (locale, access_token):
    url = 'https://us.api.blizzard.com/sc2/legacy/data/achievements/1?access_token='+access_token
    print(url)
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    #df = pd.DataFrame()
    return (r.text)

def explore_starcraft_achievements (starcraft_achievements):
    df = pd.DataFrame()
    for achievement in starcraft_achievements['achievements']:
        row = dict(title=achievement['title'], description=achievement['description'],
                   achievement_id=achievement['achievementId'], category_id=achievement['categoryId'],
                   points=achievement['points'])
        df = df.append(row, ignore_index = True)
    return df


def get_wow_profile (realm, player, token):
    url = 'https://us.api.blizzard.com/profile/wow/character/' + realm \
          + '/' + player + '?namespace=profile-us&locale=en_US&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    row = dict(id = unpacked['id'], name = unpacked['name'], gender = unpacked['gender']['name'],
          faction = unpacked['faction']['name'], race = unpacked['race']['name'],
          character_class = unpacked['character_class']['name'],
          active_spec = unpacked['active_spec']['name'], realm = unpacked['realm']['slug'],
          guild = unpacked['guild']['name'], level = unpacked['level'],
          achievement_points = unpacked['achievement_points'],
          last_login = unpacked['last_login_timestamp'],
          average_item_level = unpacked['average_item_level'],
          equipped_item_level = unpacked['equipped_item_level'])
    return row

def get_guild_roster (realm, guild, access_token):
    url = 'https://us.api.blizzard.com/data/wow/guild/'+ realm \
          + '/' + guild + '/roster?namespace=profile-us&locale=en_US&access_token=' + access_token
    r = requests.get(url)
    unpacked = unpack_json(r.text)
    
    guild_faction = unpacked['guild']['faction']['name']
    for member in unpacked['members']:
        row = dict(player = member['character']['name'], id = member['character']['id'],
              realm = member['character']['realm']['slug'], realm_id = member['character']['realm']['id'],
              level = member['character']['level'], playable_class = member['character']['playable_class']['id'],
              playable_race = member['character']['playable_race']['id'], guild_rank = member['rank'],
              guild_name = guild, faction = guild_faction)
    return row


realm = 'blackhand'
player = 'dammitpriest'
guild = 'murder-murlocs'
row = get_guild_roster (realm, guild, access_token)
print(row)
#row = get_wow_profile (realm, player, access_token)


# Example API calls
#print(get_achievement_category (namespace, locale).head())
#print(get_achievement_list (namespace, locale).head())

# Loop for realm, locale (country), and period to get a full dataset
# Look at how the rankings change over time for players and teams
# Effect of player in certain roles
# Effect of affixes and difficulty on team and individual performance
#mythic_keystone_dungeon_leaderboard_instances = get_mythic_dungeon_leaderboard_instances (11, namespace, locale)
#mythic_keystone_dungeon_leaderboard = get_mythic_keystone_dungeon_leaderboard(11, namespace, locale, 197, 641)

#TODO: Get player profiles: achievements
#TODO: Mythic raid dataset
#TODO: MDI dataset
#TODO: Esports raid dataset
#TODO: League of Legends Dataset
#TODO: Starcraft2 Dataset
#ToDO: Call of duty dataset
