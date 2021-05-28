## Research questions
- How can we determine whether an article is about the war or not?
- What are the spatial imaginaries of different newspapers in the data set?
- Are spatial imaginaries more committed to the place of publication or to the political affiliation of the newspaper?
- To what extent does a paper’s imagined geography reflect realia like transport / trade networks and, more globally, corporate/structural power (William Roy); following Blevins, 2014:132-134


## Independent tasks
### Reviewing the data (Cédric, Oleg, Nicolas, Cosmo, Farimah)
- checking issues to have an idea of what portion is about war
- check quality of named entities
- check the json and how the data is structured
- try to extract one article and one issue from the json
- Assigning political affiliations of the newspapers (David, Maelle, Suphan, Jani)


### Identifying newspaper discourses connected with place agglomerations (Maelle, Oleg, Suphan, Nicolas)
- place-name extraction + geocoding
    - pruning via outlier clipping based on similarity / density
    - frequency-based pruning
- domain validated, geospatial clustering => agglomerations (target: war zones)
- aggregate general term cooccurrences for place names by cluster / agglomeration
- aggregated cooccurrence terms feature extraction + distribution analysis across war zones+papers+years


Mapping NEs (Cédric, Nicolas, Farimah)
- reviewing data/results
- Evaluating ambiguity in NEs

Visualisations/maps (Suphan, Oleg, Cédric, Farimah)

Framing the theoretical problem, linking to historical research (David)
- WW1 and media history in general (including censorship)
    - CENSORSHIP may be reconstructed via comparing newspaper coverage of the same spatio-temporal situations, e.g. one-vs-all patterns
- List of Newspapers titles in the data dump:
  - German: `arbeiter_zeitung`, `illustrierte_kronen_zeitung`, `innsbrucker_nachrichten`, `neue_freie_presse`
  - French: `le_matin`, `l_oeuvre`, `la_fronde`
  - English: `new_york_herald`
  - Swedish: `abo_underrattelser`, `hufvudstadsbladet`, `vastra_finland`
  - Finnish: `uusi_aura`, `uusi_suometar`




## Theoretical reflections
classification dimensions: linguistic, geographic, ideological, temporal

### Spatial imaginaries
Working on spatial imaginaries is a very good idea. It is both interesting for various historiographical aspects and we can easily make a plan with precise steps for data analysis.
From my experience in college (history) we focused mainly on the French context of the war, transnational approaches are very rare (often because of the linguistic barrier, french historiography is written in french and not often translated). So this question is very interesting. [Cédric]

### Space vs Place
- "In a phenomenological sense, place has often been described as space engendered with meaning through human experience (either direct or indirect)" (Tuan, 1977; as cited in Hu et al. (2020))
- Scholars such as Yi-Fu Tuan, Denis Cosgrove, Michel de Certeau, Doreen Massey, and Edward Casey offer theoretical frameworks for how societies and individuals transform space into a particular, defined place by inscribing locations with meanings, values, feelings, and imaginings. Place is constructed through multiple channels, from lived experiences to emotional attachments to acts of naming.  (Blevins, 2014:123)
- The term imagined geography operates in the tradition of Lefebvre by positing the paper’s geography as an active process of social construction rather than a passive reflection of the world. (Blevins, 2014:123)


### Place relations in virtual or cognitive space
- "[...] texts, such as Web pages, social media posts, and news articles, can mention multiple places that are far apart and even in global scale, thereby relating these places together, often representing social, economic, and historical relationships that are non-spatially determined" (Adams, 2018; as cited in Hu et al. (2020))
- "Nebraska, Spain, Puerto Rico, Waco, Baltimore, Philadelphia, and Houston merged into a constellation of locations that readers used to craft mental maps of the world. By printing some places more than others, papers such as the Houston Daily Post continually reshaped space for nineteenth-century Americans. Johnston’s national connections and the expansive daily geography of his paper point to a larger question: How did newspapers construct space in an age of nationalizing forces?" (Blevins, 2014:123)


- "Places can be related together in texts for a variety of reasons. [following Hu et al., 2020]
  - News articles can report different events that involve multiple places: a sports team may travel from their hometown to another city for a game;
  - a company based in one country may establish a new branch office in another country (Toly et al, 2012; Sassen, 2016);
  - a natural disaster, such as hurricane and flooding, can impact multiple cities and towns."<br>
    ⟹ hence the idea of place name co-occurrences (Hecht and Raubal, 2008; Twaroch et al, 2009; Ballatore et al, 2014; Liu et al, 2014; Spitz et al, 2016).
- Differentiation between a locatum (an object in space) and a relatum (another object that the locatum is related to), which can be used by a reader in a (geo)spatial scene to orient and locate the elements described in texts (Bateman et al, 2007)


### Newspapers as a medium of geographical appreciation
* "[...] —maps of roads and rivers, letters from out-of-state relatives, or popular travelogues could all influence how people saw the world. But newspapers had the advantage of being cheap, widely available, and timely." (Blevins, 2014:128)


### Sampled content analysis
- "First, I selected a random sample of issues from the Houston Daily Post from 1894 to 1901 and overlaid an image of each of those pages with a grid of 1,200 cells.
- I then assigned each cell in the grid to a single category of content (news; advertisements; commercial data; noncommercial data; miscellaneous; and marginalia) and to multiple types of geography (Texas and its surrounding region; the Midwest; all remaining U.S. geography; and international places).
  - For example, ten cells overlaid onto a story about the Missouri, Kansas, and Texas Railroad were categorized as news content containing both Texas and Midwest geography.
  - By aggregating all 228,000 cells from the sample, I could approximate the percentage of page space dedicated to different categories of newspaper content and geographic coverage. I used this sample to produce statistically significant estimates for the entire collection, which allowed me to establish connections between content and geography in the newspaper."
  - Further reading: Spatial History Project
(Blevins, 2014:134f)



## Methodological considerations
"Harvesting geospatial data from unstructured texts has been frequently studied in geographic information retrieval (GIR) under the topic of geoparsing (Jones and Purves, 2008; Purves et al, 2018). [following (Hu et al., 2020)]

**Working hypothesis**:
- "[...] [I]n the context of a textual corpus containing documents which are associated with locations on the Earth, certain words and phrases can be more or less likely to be associated with specific locations." (Hu et al., 2020:3)
- "Newspapers print, and thereby privilege, certain places over others." (Blevins, 2014:124)
  

### Toponym recognition
One first goal would be to extract all mentions of places in articles related to the war.
We should check if the named entities for places are of good quality or not, for example by checking 100 randomly selected ones. If the quality is not good enough we could extract existing places with coordinates, for example using an online service with a python script(I know it is possible with python I did a script for that).
One other issue is that we do not know what portion of the issues talk about the war and what is not about it[e]. We could check a couple of random issues from different countries to get an idea about it but probably in Finland this is going to be a problem. If let's say more than 50 % of the articles do not concern the war it is going to be an issue and we will have to do a pre-process on the data to get the articles that only talk about war. But this in itself is a difficult task.[f] [Cédric]


We could then work on time series spatial visualization and analysis.
⟹ (PDF) Exploratory Chronotopic Data Analysis (researchgate.net)


#### Challenges (toponym recognition)
- Informal/vernacular spellings
    - https://www.yourplacenames.com/vernacular/ (Twaroch and Jones; 2010; as cited in Hu et al., (2020))
- implicit place name mentions
   - geo-indicative, but inherently non-spatial words: beach, sunshine (Adams and Janowicz, 2012)
- False positives/negatives


### Toponym resolution
- "identify the corresponding instances and the location coordinates [points, lines, and polygons] of the recognized place names." (Freire et al, 2011; Gritta et al, 2018; as cited in Hu et al., 2020:2)


#### Challenges
- place name ambiguity
- Which Washington? (Formally,) there are <u>50 candidate places</u>!
   - even worse: ambiguities with other types of entities, e.g. person names
   - (DeLozier, Baldridge, & London, 2015; Ju et al., 2016; Overell & Ruger, 2008)
- metonymy
  - "London voted to pass an act" [GOV ENTITY]


### Approaches
#### Domain Knowledge
<div>

- heuristic rules for disambiguation, e.g. by...
- total population / largest total area
- most prominent / default place instance
- administrative hierarchies; capital or main city (Ladra et al; 2008)<br>
    ⟹ Gazetteers or even general-purpose search-engines as in (Li et al; 2002) to the rescue!
</div>

- one referent per document (Leidner, 2008)
  - toponym that appears in different parts of the same document will most likely refer to the same place instance 

#### (Semi-)Automatic Inference
- Mutual/pairwise toponym co-occurrence model to disambiguate from non-toponyms (Overell and Rüger; 2008)
- Conceptual density-based toponym disambiguation using external reference GeoSemCor; (Buscaldi and Rosso; 2008)
- Ensemble methods (Lieberman and Samet; 2011)
- Feature ensembles: incorporating geospatial distances to disambiguate candidate place instances (Santos et al; 2015)


#### Location inference from language modeling 😍
- "A variety of language models have been developed for geo-referencing texts using all the terms present in a document rather than toponyms only" (Hu et al., 2020:8)
- identify locations above and beyond place names (Tenbrink and Kuhn, 2011; Stock and Yousaf, 2018); target features: spatial language, i.e. spatial prepositions, adjectives, reference frames...
- classifiers trained to predict regions & geodesic grids (Roller et al, 2012; Wing and Baldridge, 2014; Han et al, 2014)


##### Language-independent Unicode character level classifier (Adams and McKenzie, 2018)
- "[...] technique for georeferencing noisy text, such as found in colloquial social media posts and texts scanned with optical character recognition." (Adams and McKenzie, 2018:1)
- "[...] place being observed is only implicitly referenced or ambiguous. Sometimes this is due to the fact that an ambiguous place name is referenced in the text, but often there is no place name and the only clue to the location are other features that can be learned from the data" (Adams and McKenzie, 2018:2)
- "Word and n-gram-based methods start to fail once we consider the multitude of languages, noisy data (e.g., misspellings), informal language, and other character sets being used, including emoticons, to record our observations of the world." (Adams and McKenzie, 2018:2)
- A key advantage of character-based classification is that very little data pre-processing or cleaning is required to build an effective classifier. Because a deep CNN learns several levels of hierarchical features, a CNN image classifier is robust to noise in the form of individual pixels being flipped. Likewise, a character-based text classifier will be robust to noise in terms of flipped characters.
- character-level ConvNets work better for less curated user-generated texts Zhang et al. (2015:7)
- Further going: CharacterBERT: Reconciling ELMo and BERT for Word-LevelOpen-Vocabulary Representations From Characters 

➕ Hierarchical softmax based on semantic tree of place names



#### Related/Interesting Work:
- Liu et al (2014) examined place name co-occurrences in a set of news articles, and found that place relatedness in news articles has a weaker distance decay effect compared with those derived from human movements. (Hu et al., 2020)
- Zhong et al (2017) also looked into place name cooccurrences in news articles, and concluded that places are more likely to be related if they are in the same administrative level or have a part-whole relation (e.g., Seattle is part of Washington State) (Hu et al., 2020)
- Adams and Gahegan (2016) performed spatio-temporal (chronotopic) analysis on Wikipedia corpus by analyzing the co-occurrences of places and times in texts to understand the intrinsic relations between place, space, and time in narrative texts. (Hu et al., 2020)


### Literature:
- Zotero group library:
https://www.zotero.org/groups/3731545/dhh21__space_wars/library
- Hu, Yingjie & Adams, Benjamin. (2020). Harvesting Big Geospatial Data from Natural Language Texts.
- [Adams, Benjamin & McKenzie, Grant. (2018). Crowdsourcing the character of a place: Character-level convolutional networks for multilingual geographic text classification. Transactions in GIS. 22. 10.1111/tgis.12317.](https://www.researchgate.net/publication/322759551_Crowdsourcing_the_character_of_a_place_Character-level_convolutional_networks_for_multilingual_geographic_text_classification)
- [Geometric and Topological Inference](https://geometrica.saclay.inria.fr/team/Fred.Chazal/papers/CGLcourseNotes/main.pdf)
- [Homology and topological persistence](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.224.2050&rep=rep1&type=pdf)

### Labs
- [GeoAI@UB – Geospatial Artificial Intelligence Lab (buffalo.edu)](https://geoai.geog.buffalo.edu/)
- [The Edinburgh Language Technology Group (LTG)](https://www.ltg.ed.ac.uk)

### Tools:
<div>

- geotemporal exhibit-builder: https://neatline.org/ 
- https://echarts.apache.org/examples/en/index.html#chart-type-map
- https://github.com/fbdesignpro/sweetviz
- https://github.com/jupyter-widgets/ipyleaflet (mapping with Python)
- https://github.com/streamlit/streamlit (library to quickly build web app with Python, with data visualisation)
- GitHub - utcompling/WarOfTheRebellion: Annotated corpus of data from War of The Rebellion (American Civil War archives)
</div>

- [World Historical Gazetteer](http://whgazetteer.org/usingapi/)


#### General NER
<div>

- https://stanfordnlp.github.io/stanza/ner.html
- https://spacy.io/api/entityrecognizer
</div>
<div>

- https://demo.dbpedia-spotlight.org/ !!!!!!!!
- automatically links extracted entities to corresponding DBpedia concepts! i.e. immediate geolocation
- https://www.refinitiv.com/en/products/intelligent-tagging-text-analytics
</div>


#### Dedicated Geoparsers
<div>

- The Edinburgh Geoparser: https://www.ltg.ed.ac.uk/software/geoparser/ [h][i]
- https://github.com/geovista/GeoTxt (Karimzadeh et al, 2013)
- https://github.com/grantdelozier/TopoCluster (DeLozier et al, 2015)        
  - performs geoparsing without using a gazetteer!!!
  - leverages geographic profiles of words in surrounding context!
  - "The geographic profile of a word is the spatial distribution of the word characterized by local spatial statistics, and DeLozier et al (2015) derived geographic profiles of words using a set of geotagged Wikipedia articles"
</div>
<div>

- https://github.com/Novetta/CLAVIN
  - Stanford NER + OpenNLP + gazetteer + fuzzy search
</div>
<div>

- https://geocoder.readthedocs.io/
- https://www.geonames.org/
- https://geojson.org/ 
</div>
