import numpy as np

class Trained_hand_feature():
     step_1 = array([0.11637487, 0.13903193, 0.0545829 , 0.04325438, 0.04325438,
       0.04325438, 0.04325438, 0.0545829 , 0.07312049, 0.04325438,
       0.04325438, 0.04325438, 0.04325438, 0.04325438, 0.04325438,
       0.04325438, 0.04325438, 0.04325438], dtype=np.float64)
     step_2 = array([0.07826888, 0.08195212, 0.07918969, 0.04051565, 0.03959484,
       0.03867403, 0.03867403, 0.07826888, 0.10128913, 0.06906077,
       0.05709024, 0.03867403, 0.04327808, 0.03867403, 0.05616943,
       0.04327808, 0.03867403, 0.03867403], dtype=np.float64)
     step_3 = array([0.07291667, 0.06979167, 0.071875  , 0.05      , 0.04479167,
       0.04375   , 0.04375   , 0.07083333, 0.07291667, 0.06875   ,
       0.053125  , 0.040625  , 0.05208333, 0.04583333, 0.06041667,
       0.05208333, 0.04270833, 0.04375   ], dtype=np.float64)
     step_4 = array([0.06831567, 0.06360424, 0.06595995, 0.06007067, 0.04711425,
       0.04946996, 0.04946996, 0.06713781, 0.05889282, 0.06007067,
       0.05535925, 0.04711425, 0.05064782, 0.05064782, 0.05300353,
       0.05064782, 0.05182568, 0.05064782], dtype=np.float64)

    def get_step_one_strength(self):
      return Trained_hand_feature.step_1

    def get_step_two_strength(self):
      return Trained_hand_feature.step_2

    def get_step_three_strength(self):
      return Trained_hand_feature.step_3

    def get_step_four_strength(self):
      return Trained_hand_feature.step_4
