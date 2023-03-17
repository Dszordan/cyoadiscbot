import os
import yaml

class FilePersistence:
    def __init__(self, admin_state_file='./admin.yaml', decision_state_file='./decisions.yaml'):
        self.admin_template = "./model/template/admin_template.yaml"
        self.decision_template = "./model/template/decision_template.yaml"
        self.admin_state_file = admin_state_file
        self.decision_state_file = decision_state_file

        for state_file in [self.admin_state_file, self.decision_state_file]:
            if not os.path.exists(state_file):
                print(f'Creating file {state_file}.')
                self.write_template(state_file)

    # Decisions
    def write_state(self, decisions):
        with open(self.decision_state_file, 'w') as f:
            yaml.dump(decisions, f)

    def get_state(self):
        with open(self.decision_state_file) as f:
            return yaml.load(f, Loader=yaml.Loader)

    def update_decision(self, decision):
        decisions = self.get_state().get('decisions', [])
        for i, obj in enumerate(decisions):
            if obj.id_ == decision.id_:
                decisions[i] = decision
                self.write_state({'decisions': decisions})
                break
        else:
            print('Object to replace not found.')

    def write_template(self, state_file):
        with open(self.decision_template if 'decision' in state_file else self.admin_template) as f:
            state = yaml.load(f, Loader=yaml.Loader)
            print(state)

        with open(state_file, 'w') as f:
            print(f'Writing template to state file {state_file}, {state}.')
            yaml.dump(state, f)

    def get_admin_state(self):
        with open(self.admin_state_file) as f:
            return yaml.load(f, Loader=yaml.Loader)

    def write_admin_state(self, admin):
        with open(self.admin_state_file, 'w') as f:
            print(f'Writing to state file {self.admin_state_file}, {admin}.')
            yaml.dump(admin, f)