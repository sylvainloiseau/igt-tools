import pympi
from igttools.igt import Corpus, Text, Paragraph, Sentence, Word, Morph, UnitFactory
from typing import Union, List, Dict, Set

class ElanCorpoAfr():
 
  """
  Turn a set of python hashtable (dict), describing annotations, as
  produced by pympi into an IGT (hierachy of sentences, word, morphs)

  pympi produces the following structures :
  (all anotations are stored, by tier, in the tiers attribute of the
  Eaf object):
  
  >>> eafob.tiers["ref@SP1"][0]
  
  {
   'a4931': ('ts2', 'ts4',   'BEJ_MV_CONV_01_RICH_SP1_001', None),
   'a4932': ('ts5', 'ts7',   'BEJ_MV_CONV_01_RICH_SP1_002', None),
   'a4933': ('ts8', 'ts11',  'BEJ_MV_CONV_01_RICH_SP1_003', None),
   'a4934': ('ts12', 'ts15', 'BEJ_MV_CONV_01_RICH_SP1_004', None),
   'a4935': ('ts16', 'ts19', 'BEJ_MV_CONV_01_RICH_SP1_005', None),
   'a4936': ('ts20', 'ts24', 'BEJ_MV_CONV_01_RICH_SP1_006', None)
    ...
  }
  
  >>> eafob.tiers["tx@SP1"][1]
  
  {
   'a5188': ('a4931', 'əəə /', None, None),
   'a5189': ('a4932', '722', None, None),
   'a5190': ('a4933', 'suːreːne damanib /', None, None),
   'a5191': ('a4934', '832', None, None),
   'a5192': ('a4935', 'gabaha ˈtagiːfeːn //', None, None),
   'a5193': ('a4936', '1578', None, None),
   'a5194': ('a4937', 'uːn uːtaˀ /', None, None)
  ...
  }
  
  >>> eafob.tiers["mot@SP1"][1]
  
  {
   'a14879': ('a5188', 'əəə', None, None),
   'a14880': ('a5188', '/', 'a14879', None),
   'a14881': ('a5189', '722', None, None),
   'a14882': ('a5190', 'suːreːneː', None, None),
   'a14883': ('a5190', 'idamaːniːb', 'a14882', None),
   'a14884': ('a5190', '/', 'a14883', None),
   'a14885': ('a5191', '832',None, None),
   'a14886': ('a5192', 'gaba', None, None),
   'a14887': ('a5192', 'ahaː', 'a14886', None),
   'a14888': ('a5192', 'tak', 'a14887', None),
   'a14889': ('a5192', 'iːfi', 'a14888', None),
   'a14890': ('a5192', 'eːn', 'a14889', None),
   'a14891': ('a5192', '//', 'a14890', None),
   'a14892': ('a5193', '1578', None, None)
  ...
  }
  
  >>> eafob.tiers["mb@SP1"][1]
  {
   'a15525': ('a14879', 'əəə', None, None),
   'a15526': ('a14880', '/', None, None),
   'a15527': ('a14882', 'suːr', None, None),
   'a15528': ('a14882', '-eː', 'a15527', None),
   'a15529': ('a14882', '-n', 'a15528', None),
   'a15530': ('a14882', '-eː', 'a15529', None),
   'a15531': ('a14883', 'i=', None, None),
   'a15532': ('a14883', 'damaːn', 'a15531', None),
   'a15533': ('a14883', '=iːb', 'a15532', None),
  
  >>> eafob.tiers["ge@SP1"][1]
  
  {
    'a16444': ('a15525', 'er', None, None),
    'a16445': ('a15527', 'before', None, None),
    'a16446': ('a15528', '-GEN.PL', None, None),
    'a16447': ('a15529', '-L', None, None),
    'a16448': ('a15530', '-GEN.PL', None, None),
    'a16449': ('a15531', 'DEF.M=', None, None),
    'a16450': ('a15532', 'time', None, None),
    'a16451': ('a15533', '=LOC.SG', None, None),
  
  >>> eafob.tiers["ft@SP1"][1]
  {
    'a6091': ('a4931', 'Er,', None, None),
    'a6092': ('a4932', '', None, None),
    'a6093': ('a4933', 'In the old days', None, None),

  """

  def __init__(self, filename):
    """
    Produce a list of sentences. Sentences are a dict with entries
    "ft", "participant", "timestamp", "words" :
    

     {'ft': 'I used to solve them.',
      'id': 'a18309',
      'participant': 'SP2',
      'timestamp': ('ts2476',),
      'words': [{'morphemes': [
                               {'gls': 'solve', 'id': 'a18724', 'txt': 'hillinaːhi'},
                               {'gls': '-AOR.1SG', 'id': 'a18725', 'txt': '-i'}
                              ]
                },
                {'morphemes': [ {'gls': '.', 'id': 'a18726', 'txt': '//'}]}
               ]
    },

    """
    eafob = pympi.Elan.Eaf(filename)		
    self.filename = filename
    self.eafob = eafob
    self.factory = UnitFactory()

    # the set of the participant (used as suffix on tier name: mb@SP1,
    # mb@SP2, etc).
    self.participants = self._get_participants()

    # Turn the pympi data structures, organized by  tier, into a
    # hierarchical structures of ids (sentences -> words -> morphems)
    # for each participant
    self.ids = { p: self._get_ids_by_participant(p) for p in self.participants }

    # Turn the hierarchical structure of ids into actual sentences:
    sentences = []
    for p in self.participants:
      if self.ids[p] is not None:
        sentences = sentences + self._get_sentences(p)

    # order the sentences of the text by their timestamp
    sentences = self._order_sentences(sentences)

    # group sentences into paragraphs. Paragraphs are made of
    # consecutive sentences by the same spaker.
    paragraphs = self._make_paragraphs_with_speaker(sentences)

    self.paragraphs = paragraphs

  def get_igt(self) -> Corpus:
      text = Text({"source" : self.filename}, self.paragraphs)
      #fields = {'paragraph' : ["speaker"], 'morph' : ["txt", "gls", "id"], 'sentence' : ["id", "ft", "participant", "timestamp"]}
      return(Corpus({}, [text]))

  def _make_paragraphs_with_speaker(self, sentences : List[Sentence]) -> List[Paragraph]:
    """
    Group consecutive sentences by same speaker into paragraph

    :param List[Sentence] sentences: the sentence to be grouped. Sentence must have a "participant" slot.
    
    :return a list of Paragraph
    """
    paragraphs: List[Paragraph] = []
    collected_sentences: List[Sentence] = []
    current_speaker: str = sentences[0].get_properties()["participant"]
    for s in sentences:
        speaker = s.get_properties()["participant"]
        if speaker != current_speaker:
            paragraphs.append(self.factory.createParagraph({"speaker": current_speaker}, collected_sentences))
            current_speaker = speaker
            collected_sentences = []
        collected_sentences.append(s)
    if len(collected_sentences) > 0:
        paragraphs.append(self.factory.createParagraph({"speaker": current_speaker}, collected_sentences))
    return(paragraphs)
            
  def _order_sentences(self, sentences : List[Sentence]) -> List[Sentence]:
      sorted_sentences = sorted(
          sentences,
          key=lambda x : self.eafob.timeslots[ x.get_properties()["timestamp"][0] ]
        )
      return(sorted_sentences)
  
  def _get_ids_by_participant(self, participant : str) -> Union[Dict[str, Dict[str, str]], None]:
    mb_tier = "mb" + "@" + participant
    ge_tier = "ge" + "@" + participant
    mot_tier = "mot" + "@" + participant
    tx_tier = "tx" + "@" + participant
    ft_tier = "ft" + "@" + participant

    if mb_tier not in self.eafob.tiers:
      #the participant exist but it does not have any actual annotation
      return None

    # map morph transcription ('əəə') with morphem id ('a15525')
    # in eafob.tiers[mb_tier][1] :
    # {
    #  'a15525': ('a14879', 'əəə', None, None),
    mb_by_mb_ids = dict()
    for k, v in self.eafob.tiers[mb_tier][1].items():
      mb_by_mb_ids[k] = v[1]
    
    # map glose value ('er') with morphem id ('a15525')
    # in self.eafob.tiers[ge_tier][1] :
    # {
    #   'a16444': ('a15525', 'er', None, None),
    ge_by_mb_ids = dict()
    for v in self.eafob.tiers[ge_tier][1].values():
      ge_by_mb_ids[ v[0] ] = v[1]
    
    # group morphems ids by word ids, i.e. 'a14882' : ['a15527', 'a15528'] :
    #
    # in eafob.tiers[mb_tier][1] :
    # {
    # [...]
    #  'a15527': ('a14882', 'suːr', None, None),
    #  'a15528': ('a14882', '-eː', 'a15527', None),
    # 
    mb_ids_by_word_ids: Dict[str, List[str]] = {v[0]:[] for v in self.eafob.tiers[mb_tier][1].values()}
    for k,v in self.eafob.tiers[mb_tier][1].items():
      mb_ids_by_word_ids[v[0]].append(k)
    
    words_ids_by_tx_id: Dict[str, List[str]]  = {v[0]:[] for v in self.eafob.tiers[mot_tier][1].values()}
    for k,v in self.eafob.tiers[mot_tier][1].items():
      words_ids_by_tx_id[v[0]].append(k)

    tx_ids_by_ref_ids : Dict[str, str]= dict()
    for k, v in self.eafob.tiers[tx_tier][1].items():
      tx_ids_by_ref_ids[v[0]] = k
    
    ft_by_ref_ids : Dict[str, str] = dict()
    for v in self.eafob.tiers[ft_tier][1].values():
      ft_by_ref_ids[v[0]] = v[1]

    res = {
      "mb_by_mb_ids" : mb_by_mb_ids,
      "ge_by_mb_ids" : ge_by_mb_ids,
      "mb_ids_by_word_ids" : mb_ids_by_word_ids,
      "words_ids_by_tx_id" : words_ids_by_tx_id,
      "tx_ids_by_ref_ids" : tx_ids_by_ref_ids,
      "ft_by_ref_ids" : ft_by_ref_ids
    }
    return res

  def _get_participants(self) -> Set[str]:
      v = [x.split("@") for x in self.eafob.tiers.keys()]
      p = [x[1] for x in v if len(x) > 1]
      return(set(p))

  def _get_words(self, word_ids, mb_ids_by_word_ids, mb_by_mb_ids, ge_by_mb_ids) -> List[Word]:
      words = list()
      for word_id in word_ids:
        item: Dict[str, str] = dict()
        morphemes: List[Morph] = []
        if word_id in mb_ids_by_word_ids:
          mb_ids = mb_ids_by_word_ids[word_id]#().sort()
          if mb_ids is not None:
            for mb_id in mb_ids:
              morphemes.append(
                self.factory.createMorph({
                  "txt" : mb_by_mb_ids[mb_id] if mb_id in mb_by_mb_ids else None,
                  "gls" : ge_by_mb_ids[mb_id] if mb_id in ge_by_mb_ids else None,
                  "id" :  mb_id
                })
              )
        words.append(self.factory.createWord(item, morphemes))
      return words

  def _get_sentences(self, participant_name: str) -> List[Sentence]:
    sentences : List[Sentence] = []
    participant_ids = self.ids[participant_name]
    for sentence_id in participant_ids["ft_by_ref_ids"].keys():
      item = dict()
      item["id"] = sentence_id
      item["ft"] = participant_ids["ft_by_ref_ids"][sentence_id]
      item["participant"] = participant_name
      item["timestamp"] = self.eafob.tiers["ref@" + participant_name][0][sentence_id][0:1]
      
      #id of the associated annotation on the "tx" tier:
      tx_id = participant_ids["tx_ids_by_ref_ids"][sentence_id]
      
      #ids of the word of that sentence
      word_ids = participant_ids["words_ids_by_tx_id"][str(tx_id)] # ().sort()
      
      if word_ids is not None:
          words = self._get_words(
                  word_ids,
                  participant_ids["mb_ids_by_word_ids"],
                  participant_ids["mb_by_mb_ids"],
                  participant_ids["ge_by_mb_ids"]
                  )
      sentences.append(self.factory.createSentence(item, words))
    return(sentences)
