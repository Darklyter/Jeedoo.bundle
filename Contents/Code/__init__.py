# Jeedoo.com
# Update: 19 January 2019
# Description: New updates from a lot of diffrent forks and people. Please read README.md for more details.
import re
import datetime
import random

# preferences
preference = Prefs
DEBUG = preference['debug']
if DEBUG:
  Log('Agent debug logging is enabled!')
else:
  Log('Agent debug logging is disabled!')

# URLS
ADE_BASEURL = 'https://www.jeedoo.com'
if preference['includegay'] == 'no':
    ADE_SEARCH_MOVIES = ADE_BASEURL + '/porn-movies/?show_no_offer=1&search=%s'
elif preference['includegay'] == 'yes':
    ADE_SEARCH_MOVIES = ADE_BASEURL + '/?show_no_offer=1&search=%s'
elif preference['includegay'] == 'only':
    ADE_SEARCH_MOVIES = ADE_BASEURL + '/gay-porn-movies/?show_no_offer=1&search=%s'
else:
    ADE_SEARCH_MOVIES = ADE_BASEURL + '/porn-movies/?show_no_offer=1&search=%s'

ADE_MOVIE_INFO = ADE_BASEURL + '/product/%s'

scoreprefs = int(preference['goodscore'].strip())
if scoreprefs > 1:
    GOOD_SCORE = scoreprefs
else:
    GOOD_SCORE = 98
if DEBUG:Log('Result Score: %i' % GOOD_SCORE)

INITIAL_SCORE = 100

titleFormats = r'\(DVD\)|\(Blu-Ray\)|\(BR\)|\(VOD\)|\(Gay DVD\)'

def Start():
  HTTP.CacheTime = CACHE_1MINUTE
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

def ValidatePrefs():
  pass

class JeedooAgent(Agent.Movies):
  name = 'Jeedoo'
  languages = [Locale.Language.English]
  primary_provider = True

  def search(self, results, media, lang):
    title = media.name

    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    query = String.URLEncode(String.StripDiacritics(title.replace('-','')))

    # resultarray[] is used to filter out duplicate search results
    resultarray=[]
    if DEBUG: Log('Search Query: %s' % str(ADE_SEARCH_MOVIES % query))
    # Finds the entire media enclosure <DIV> elements then steps through them
    if DEBUG: Log('Looking for Movies...')
    ADE_SEARCH_STRING = (ADE_SEARCH_MOVIES % query)
    for movie in HTML.ElementFromURL(ADE_SEARCH_STRING).xpath('//div[@class="col-xs-60 search_list_item"]'):
        # curName = The text in the 'title' p
        moviehref = movie.xpath('./h4/a[@class="text-default strong"]')[0]
        curName = moviehref.text_content().strip()
        if curName.count(', The'):
          curName = 'The ' + curName.replace(', The','',1)
        curName += " [JC]"

        # curID = the ID portion of the href in 'movie'
        curID = moviehref.get('href').split('/',2)[2]
        curID = re.findall('\d+',curID)[0]
        score = INITIAL_SCORE - Util.LevenshteinDistance(title.lower(), curName.lower())
        if DEBUG: Log('Movie Found: %s \t ID: %s\t Score: %s' % (str(curName), str(curID),str(score)))

        if curName.lower().count(title.lower()):
            results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))
        elif (score >= GOOD_SCORE):
            results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    html = HTML.ElementFromURL(ADE_MOVIE_INFO % metadata.id)
    metadata.title = media.title
    metadata.title = re.sub(r'\ \[JC\]','',metadata.title).strip()
    metadata.title = re.sub(titleFormats,'',metadata.title).strip()
    if DEBUG: Log('Updating Title: %s' % metadata.title)

    # Thumb and Poster
    imgpath = html.xpath('//img[@id="pi"]/@src')[0]
    thumbpath = html.xpath('//img[@id="pi"]/@src')[0]
    Log('Image URL: %s' % imgpath)
    thumb = HTTP.Request(thumbpath)
    metadata.posters[imgpath] = Proxy.Preview(thumbpath)

    # Tagline
    try: metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].strip()
    except: pass

    # Summary.
    try:
      for summary in html.xpath('//div[@class="text-center fsize14"]/text()'):
        metadata.summary = summary.strip()
    except: pass

    # Studio.
    try:
      for studio in html.xpath('//td[contains(text(),"Label:")]/following-sibling::td/a/text()[1]'):
        metadata.studio = studio.strip()
        if DEBUG: Log('Added Studio: %s' % studio.strip())
    except: pass

    # Release Date.
    try:
      for releasedate in html.xpath('//td[contains(text(),"Release date:")]/following-sibling::td/text()[1]'):
        metadata.originally_available_at = Datetime.ParseDate(releasedate.strip()).date()
        metadata.year = metadata.originally_available_at.year
    except: pass

    # Cast - added updated by Briadin / 20190108
    try:
      metadata.roles.clear()
      for castmember in html.xpath('//td[contains(text(),"Cast:")]/following-sibling::td/a/text()'):
          role = metadata.roles.new()
          role.name = castmember.strip()
          if DEBUG: Log('Added Star: %s' % castmember.strip())
    except: pass
