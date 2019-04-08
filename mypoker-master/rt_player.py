from pypokerengine.players import BasePokerPlayer
from randomplayer import RandomPlayer
from numpy import np
from time import sleep
import pprint
import collections
from feature_strength_offline import FeatureStrengthOffline

class RTPlayer(BasePokerPlayer):

  def __init__(self):
    self.pp = pprint.PrettyPrinter(indent=2)
    self.hole_card = []
    # stack record keep two player's stack from last round
    self.stack_record = [['py1 last stack', 'py1 current stack'],['py2 last stack', 'py2 current stack']]
    # seat_id records the position of this player in the seat list (0/1)
    self.seat_id = 0

  def declare_action(self, valid_actions, hole_card, round_state):
    # check if raise 4 times alr, cannot raise any more
    # flag is true -- still can raise, otherwise cannot
    flag = True
    current_round = round_state['action_histories'][round_state['street']]
    uuid1 = round_state['seats'][0]['uuid']
    uuid2 = round_state['seats'][1]['uuid']
    # raise count for current round
    raiseCount = collections.defaultdict(int)
    for action_details in current_round:
        if action_details['action'] is 'RAISE' or 'BIGBLIND':
            # Big blind is also considered as 'RAISE'
            raiseCount[action_details['uuid']] += 1

    if raiseCount[uuid1] >= 4 or raiseCount[uuid2] >= 4:
        flag = False


    for i in valid_actions:
        if i["action"] == "raise":
            action = i["action"]
            return action  # action returned here is sent to the poker engine
    action = valid_actions[1]["action"]
    return action # action returned here is sent to the poker engine

  def receive_game_start_message(self, game_info):
    pass

  def receive_round_start_message(self, round_count, hole_card, seats):
    self.hole_card = hole_card
    pass

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, action, round_state):
    pass

  def receive_round_result_message(self, winners, hand_info, round_state):
    # check result and determine who is the winner
    result = 1 if winners[0]['uuid'] is self.uuid else 0

    # start training at the end of every round

    if round_state['round_count'] is 1:
        # initialise stack record when enters the first round
        initial_stack = (round_state['seats'][0]['stack'] + round_state['seats'][1]['stack'])/2
        if round_state['seats'][0]['uuid'] is self.uuid:
            self.seat_id = 0;
        else:
            self.seat_id = 1;

        assert(self.seat_id in [0,1])

        self.stack_record = [[initial_stack, round_state['seats'][0]['stack']],
                             [initial_stack, round_state['seats'][1]['stack']]]
    else:
        self.stack_record = [[self.stack_record[0][1], round_state['seats'][0]['stack']],
                             [self.stack_record[1][1], round_state['seats'][1]['stack']]]

    reward = self.stack_record[self.seat_id][1] - self.stack_record[self.seat_id][0]

    
    pass

  # feature range: 0-1
  # Input:
  # state
  #   hand: my estimated hand strength
  #   isSB: boolean true if the player if Small Blind
  #   isMe: boolean indicating whether the position is me, or opponent (using uuid) ← if this is opponent, can learn from opponent’s behavior
  #   money in the pot
  #   my current bet
  #   opponent’s current bet
  # action
  #   action: Fold:0, Call: 0.5, Raise: 1
  # Output:
  #   numpy array containing features describing a state and action
  def phi(self, card_strength, isMe, mystack, total_amount, curr_action):
    return np.array([1, # for convenience purpose
                     card_strength if curr_action is not 'fold' else 0, # 1. contains 18 feature representations, should normalised to 1,
                     # since the model will learn better if all the features have about the same magnitudes
                     # 2. when the action is fold, the particular holding doesn't have any effect on the result (neglecting minor card removal effects)
                     1 if curr_action is 'raise' else 0.5 if curr_action is 'call' else 0,
                     1 if isMe else 0,
                     1 if isMe and curr_action is 'raise',
                     mystack/total_amount if isMe else 1-mystack/total_amount,
                     ])

  # Inputs:
  #   theta: vector of parameters of our model
  #   phi: vector of features
  # Output:
  #   Qhat(phi; theta), an estimate of the action-value
  def evalModel(self, theta, phi):
    return np.sum(theta * phi)

  # Input:
  #   nRound: total number of rounds playing
  #   i: current round
  # Output:
  #   Fraction of the time we should choose our action randomly.
  # This is because we need to take all the actions in all the states at least occasionally if we want to end up with good estimates of each possibility's value
  # To do this, we can have the players act randomly some fraction epsilon of the time, otherwise use their (current-estimated) best options.
  # epsilon will shrink over time
  def epsilon(self, nRounds, i):
    return (nRounds - i) / nRounds

  # Input:
  #   theta: parameter for current model Qhat
  #   hand: hand number
  #   isMe: boolean, True for the player, False for opponents.
  #   epsilon: chance of making a random move
  # Output:
  #   A tuple of form (isGII, qhat, phi) describing the action
  #   taken, its value, and its feature vector.
  def act(self, theta, card_strength, isMe, potMoney, myBet, oppoBet, curr_action, epsilon_v):

    # feature vector for different action
    phiRAISE = self.phi(card_strength, isMe, potMoney, myBet, oppoBet, 'raise')
    phiCALL = self.phi(card_strength, isMe, potMoney, myBet, oppoBet, 'call')
    phiFOLD = self.phi(card_strength, isMe, potMoney, myBet, oppoBet, 'fold')

    # value for taking different action
    qRAISE = self.evalModel(theta, phiRAISE)
    qCALL = self.evalModel(theta, phiRAISE)
    qFOLD = self.evalModel(theta, phiFOLD)

    # choose the action with highest value as the next action
    next_action = 'raise'
    if qRAISE > np.amax([qCALL, qFOLD]):
        next_action = 'raise'
    elif qCALL > np.amax([qRAISE, qFOLD]):
        next_action = 'call'
    else:
        next_action = 'fold'

    actions = ['raise', 'call', 'fold']
    remain_actions = []
    for act in actions:
        if act is not next_action:
            remain_actions.append(act)
    assert len(remain_actions) is 2

    # determine whether the next action need to be randomly choosen
    if np.random.rand() < epsilon_v/2:
        # choose another action rather than the chosen one
        if np.random.rand() < 0.5:
           next_action = remain_actions[0]
        else:
          next_action = remain_actions[1]

    if next_action is 'raise':
        return next_action, qRAISE, phiRAISE
    elif next_action is 'call':
        return next_action, qCALL, phiCALL
    else:
        return next_action, qFOLD, phiFOLD

  # Input:
  #   stack: stack size
  #   myHandStrength: the estimated strength of my hand
  #   myAction: boolean indicating player's action
  #   oppoHand: the estimated strength of my hand (may bot be known)
  #   oppoAction: boolean indicating opponent's action
  # Output:
  #   A tuple of the form (player value, opponent value) indicating each player's
  #   stack size at the end of the hand.
  def simulateHand(self, stack, myHand, myAction, oppoHand, oppoAction):
    if myAction is 'fold':
        return (stack-0.5, stack+0.5)
    if oppoAction is 'fold':
        return (stack+1, stack-1)
    # GII. Note: neglecting chops!
   # sbEquity = pfeqs[sbHand, bbHand]
    if np.random.rand() < 0.5:
        return (2*stack, 0)
    return (0, 2*stack)

  # Input:
  #     stack: my stack size
  #     nRounds: number of rounds
  #     alpha: learning rate hyperparameter
  # Output:
  #     An 8-vector of weights parameterising our linear model
  # This function implements Monte Carlo algorithm and returns the parameter theta of the model we learn
  def mc(self, stack, nRounds, alpha):
      nParams = 8
      theta = np.random.rand(nParams)



def setup_ai():
  return RandomPlayer()
