import yaml
from model.decision import Decision, DecisionState
class file_persistence:
    def __init__(self, filename):
        self.filename = filename
    
    def write_state(self, decisions):
        with open(self.filename, 'w') as f:
            f.write(yaml.dump(decisions))
    
    def get_state(self):
        with open(self.filename) as f:
            decisions = yaml.load(f.read(), Loader=yaml.Loader)
            return decisions