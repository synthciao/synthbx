
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'programCOLON COMMA DECL DOT EQ GE GT IDENT IF INPUT_DECL INTEGER LE LPAREN LT NE NOT NUMBER OUTPUT_DECL RPAREN SEMICOLON STRING SUBTYPE SYMBOL TYPE UNDERSCOREprogram : unit_listunit_list : unit\n            | unit unit_listunit : type_decl\n            | relation_decl\n            | directive\n            | rule\n            | facttype_decl : TYPE IDENT\n            | TYPE IDENT SUBTYPE type_name\n            | TYPE IDENT EQ type_namerelation_decl : DECL IDENT LPAREN attribute_decl_list RPAREN\n        | DECL IDENT LPAREN RPARENdirective : INPUT_DECL ident_list\n            | OUTPUT_DECL ident_listrule : head IF body DOTfact : atom DOThead : atombody : conjunction\n        | conjunction SEMICOLON conjunction_listconjunction_list : conjunction\n            | conjunction SEMICOLON conjunction_listconjunction : item\n            | item COMMA item_listitem_list : item\n            | item COMMA item_listitem : atom\n            | negation\n            | constraintatom : IDENT LPAREN argument_list RPAREN\n            | IDENT LPAREN RPARENnegation : NOT atomconstraint : variable EQ constant\n            | variable NE constant\n            | variable GT constant\n            | variable LT constant\n            | variable GE constant\n            | variable LE constantident_list : IDENT\n            | IDENT COMMA ident_listattribute_decl_list : attribute_decl\n            | attribute_decl COMMA attribute_decl_listattribute_decl : IDENT COLON type_nametype_name : NUMBER \n            | SYMBOL \n            | IDENTargument_list : argument\n            | argument COMMA argument_listargument : variable\n            | constantvariable : IDENT \n            | UNDERSCOREconstant : STRING\n            | INTEGER'
    
_lr_action_items = {'TYPE':([0,3,4,5,6,7,8,17,20,21,22,24,47,48,49,50,51,56,58,59,71,],[9,9,-4,-5,-6,-7,-8,-9,-14,-39,-15,-17,-46,-10,-44,-45,-11,-13,-40,-16,-12,]),'DECL':([0,3,4,5,6,7,8,17,20,21,22,24,47,48,49,50,51,56,58,59,71,],[11,11,-4,-5,-6,-7,-8,-9,-14,-39,-15,-17,-46,-10,-44,-45,-11,-13,-40,-16,-12,]),'INPUT_DECL':([0,3,4,5,6,7,8,17,20,21,22,24,47,48,49,50,51,56,58,59,71,],[12,12,-4,-5,-6,-7,-8,-9,-14,-39,-15,-17,-46,-10,-44,-45,-11,-13,-40,-16,-12,]),'OUTPUT_DECL':([0,3,4,5,6,7,8,17,20,21,22,24,47,48,49,50,51,56,58,59,71,],[13,13,-4,-5,-6,-7,-8,-9,-14,-39,-15,-17,-46,-10,-44,-45,-11,-13,-40,-16,-12,]),'IDENT':([0,3,4,5,6,7,8,9,11,12,13,17,18,20,21,22,23,24,25,26,36,37,45,47,48,49,50,51,53,56,58,59,60,61,70,71,72,85,86,],[10,10,-4,-5,-6,-7,-8,17,19,21,21,-9,27,-14,-39,-15,44,-17,47,47,54,21,10,-46,-10,-44,-45,-11,27,-13,-40,-16,44,44,47,-12,54,44,44,]),'$end':([1,2,3,4,5,6,7,8,16,17,20,21,22,24,47,48,49,50,51,56,58,59,71,],[0,-1,-2,-4,-5,-6,-7,-8,-3,-9,-14,-39,-15,-17,-46,-10,-44,-45,-11,-13,-40,-16,-12,]),'LPAREN':([10,19,44,],[18,36,18,]),'IF':([14,15,29,52,],[23,-18,-31,-30,]),'DOT':([15,29,34,35,38,39,40,41,42,43,52,62,73,74,75,76,77,78,79,80,81,82,87,88,],[24,-31,-53,-54,59,-19,-23,-27,-28,-29,-30,-32,-21,-20,-25,-24,-33,-34,-35,-36,-37,-38,-22,-26,]),'SUBTYPE':([17,],[25,]),'EQ':([17,33,44,46,],[26,-52,-51,63,]),'RPAREN':([18,27,28,30,31,32,33,34,35,36,47,49,50,55,57,69,83,84,],[29,-51,52,-47,-49,-50,-52,-53,-54,56,-46,-44,-45,71,-41,-48,-43,-42,]),'UNDERSCORE':([18,23,53,60,61,85,86,],[33,33,33,33,33,33,33,]),'STRING':([18,53,63,64,65,66,67,68,],[34,34,34,34,34,34,34,34,]),'INTEGER':([18,53,63,64,65,66,67,68,],[35,35,35,35,35,35,35,35,]),'COMMA':([21,27,29,30,31,32,33,34,35,40,41,42,43,47,49,50,52,57,62,75,77,78,79,80,81,82,83,],[37,-51,-31,53,-49,-50,-52,-53,-54,61,-27,-28,-29,-46,-44,-45,-30,72,-32,86,-33,-34,-35,-36,-37,-38,-43,]),'NOT':([23,60,61,85,86,],[45,45,45,45,45,]),'NUMBER':([25,26,70,],[49,49,49,]),'SYMBOL':([25,26,70,],[50,50,50,]),'SEMICOLON':([29,34,35,39,40,41,42,43,52,62,73,75,76,77,78,79,80,81,82,88,],[-31,-53,-54,60,-23,-27,-28,-29,-30,-32,85,-25,-24,-33,-34,-35,-36,-37,-38,-26,]),'NE':([33,44,46,],[-52,-51,64,]),'GT':([33,44,46,],[-52,-51,65,]),'LT':([33,44,46,],[-52,-51,66,]),'GE':([33,44,46,],[-52,-51,67,]),'LE':([33,44,46,],[-52,-51,68,]),'COLON':([54,],[70,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'program':([0,],[1,]),'unit_list':([0,3,],[2,16,]),'unit':([0,3,],[3,3,]),'type_decl':([0,3,],[4,4,]),'relation_decl':([0,3,],[5,5,]),'directive':([0,3,],[6,6,]),'rule':([0,3,],[7,7,]),'fact':([0,3,],[8,8,]),'head':([0,3,],[14,14,]),'atom':([0,3,23,45,60,61,85,86,],[15,15,41,62,41,41,41,41,]),'ident_list':([12,13,37,],[20,22,58,]),'argument_list':([18,53,],[28,69,]),'argument':([18,53,],[30,30,]),'variable':([18,23,53,60,61,85,86,],[31,46,31,46,46,46,46,]),'constant':([18,53,63,64,65,66,67,68,],[32,32,77,78,79,80,81,82,]),'body':([23,],[38,]),'conjunction':([23,60,85,],[39,73,73,]),'item':([23,60,61,85,86,],[40,40,75,40,75,]),'negation':([23,60,61,85,86,],[42,42,42,42,42,]),'constraint':([23,60,61,85,86,],[43,43,43,43,43,]),'type_name':([25,26,70,],[48,51,83,]),'attribute_decl_list':([36,72,],[55,84,]),'attribute_decl':([36,72,],[57,57,]),'conjunction_list':([60,85,],[74,87,]),'item_list':([61,86,],[76,88,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> program","S'",1,None,None,None),
  ('program -> unit_list','program',1,'p_program','parser.py',8),
  ('unit_list -> unit','unit_list',1,'p_unit_list','parser.py',13),
  ('unit_list -> unit unit_list','unit_list',2,'p_unit_list','parser.py',14),
  ('unit -> type_decl','unit',1,'p_unit','parser.py',22),
  ('unit -> relation_decl','unit',1,'p_unit','parser.py',23),
  ('unit -> directive','unit',1,'p_unit','parser.py',24),
  ('unit -> rule','unit',1,'p_unit','parser.py',25),
  ('unit -> fact','unit',1,'p_unit','parser.py',26),
  ('type_decl -> TYPE IDENT','type_decl',2,'p_type_decl','parser.py',31),
  ('type_decl -> TYPE IDENT SUBTYPE type_name','type_decl',4,'p_type_decl','parser.py',32),
  ('type_decl -> TYPE IDENT EQ type_name','type_decl',4,'p_type_decl','parser.py',33),
  ('relation_decl -> DECL IDENT LPAREN attribute_decl_list RPAREN','relation_decl',5,'p_relation_decl','parser.py',43),
  ('relation_decl -> DECL IDENT LPAREN RPAREN','relation_decl',4,'p_relation_decl','parser.py',44),
  ('directive -> INPUT_DECL ident_list','directive',2,'p_directive','parser.py',52),
  ('directive -> OUTPUT_DECL ident_list','directive',2,'p_directive','parser.py',53),
  ('rule -> head IF body DOT','rule',4,'p_rule','parser.py',58),
  ('fact -> atom DOT','fact',2,'p_fact','parser.py',63),
  ('head -> atom','head',1,'p_head','parser.py',74),
  ('body -> conjunction','body',1,'p_body','parser.py',79),
  ('body -> conjunction SEMICOLON conjunction_list','body',3,'p_body','parser.py',80),
  ('conjunction_list -> conjunction','conjunction_list',1,'p_conjunction_list','parser.py',88),
  ('conjunction_list -> conjunction SEMICOLON conjunction_list','conjunction_list',3,'p_conjunction_list','parser.py',89),
  ('conjunction -> item','conjunction',1,'p_conjunction','parser.py',97),
  ('conjunction -> item COMMA item_list','conjunction',3,'p_conjunction','parser.py',98),
  ('item_list -> item','item_list',1,'p_item_list','parser.py',106),
  ('item_list -> item COMMA item_list','item_list',3,'p_item_list','parser.py',107),
  ('item -> atom','item',1,'p_item','parser.py',115),
  ('item -> negation','item',1,'p_item','parser.py',116),
  ('item -> constraint','item',1,'p_item','parser.py',117),
  ('atom -> IDENT LPAREN argument_list RPAREN','atom',4,'p_atom','parser.py',122),
  ('atom -> IDENT LPAREN RPAREN','atom',3,'p_atom','parser.py',123),
  ('negation -> NOT atom','negation',2,'p_negation','parser.py',131),
  ('constraint -> variable EQ constant','constraint',3,'p_constraint','parser.py',136),
  ('constraint -> variable NE constant','constraint',3,'p_constraint','parser.py',137),
  ('constraint -> variable GT constant','constraint',3,'p_constraint','parser.py',138),
  ('constraint -> variable LT constant','constraint',3,'p_constraint','parser.py',139),
  ('constraint -> variable GE constant','constraint',3,'p_constraint','parser.py',140),
  ('constraint -> variable LE constant','constraint',3,'p_constraint','parser.py',141),
  ('ident_list -> IDENT','ident_list',1,'p_ident_list','parser.py',146),
  ('ident_list -> IDENT COMMA ident_list','ident_list',3,'p_ident_list','parser.py',147),
  ('attribute_decl_list -> attribute_decl','attribute_decl_list',1,'p_attribute_decl_list','parser.py',155),
  ('attribute_decl_list -> attribute_decl COMMA attribute_decl_list','attribute_decl_list',3,'p_attribute_decl_list','parser.py',156),
  ('attribute_decl -> IDENT COLON type_name','attribute_decl',3,'p_attribute_decl','parser.py',164),
  ('type_name -> NUMBER','type_name',1,'p_type_name','parser.py',169),
  ('type_name -> SYMBOL','type_name',1,'p_type_name','parser.py',170),
  ('type_name -> IDENT','type_name',1,'p_type_name','parser.py',171),
  ('argument_list -> argument','argument_list',1,'p_argument_list','parser.py',176),
  ('argument_list -> argument COMMA argument_list','argument_list',3,'p_argument_list','parser.py',177),
  ('argument -> variable','argument',1,'p_argument','parser.py',185),
  ('argument -> constant','argument',1,'p_argument','parser.py',186),
  ('variable -> IDENT','variable',1,'p_variable','parser.py',191),
  ('variable -> UNDERSCORE','variable',1,'p_variable','parser.py',192),
  ('constant -> STRING','constant',1,'p_constant','parser.py',197),
  ('constant -> INTEGER','constant',1,'p_constant','parser.py',198),
]
