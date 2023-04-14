import logging
import os
import yaml
class file_persistence:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.admin_template = "./model/template/admin_template.yaml"
        self.decision_template = "./model/template/decision_template.yaml"
        self.admin_state_file = './admin.yaml'
        self.decision_state_file = './decisions.yaml'
        if(not os.path.exists(self.admin_state_file)):
            logging.info(f'Creating file {self.admin_state_file}.')
            self.write_admin_template()
        if(not os.path.exists(self.decision_state_file)):
            logging.info(f'Creating file {self.decision_state_file}.')
            self.write_decision_template()

    # Decisions    
    def write_state(self, decisions):
        with open(self.decision_state_file, 'w') as f:
            f.write(yaml.dump(decisions))
    
    def get_state(self):
        with open(self.decision_state_file) as f:
            decisions = yaml.load(f.read(), Loader=yaml.Loader)
            return decisions
    
    def update_decision(self, decision):
        logging.info(f'Updating decision {decision.id_}, {decision}.')
        decisions = self.get_state()
        # Find index of object to replace in the list
        index = -1
        for i, obj in enumerate(decisions['decisions']):
            if obj.id_ == decision.id_:
                index = i
                break

        if index != -1:
            # Replace object at the found index
            decisions['decisions'][index] = decision

            self.write_state(decisions)
        else:
            logging.error('Object to replace not found.')

    def write_decision_template(self):
        with open(self.decision_template) as f:
            decision = yaml.load(f.read(), Loader=yaml.Loader)
        
        with open(self.decision_state_file, 'w') as f:
            logging.info(f'Writing template to state file {self.decision_state_file}, {decision}.')
            f.write(yaml.dump(decision))
    
    def write_admin_state(self, admin):
        with open(self.admin_state_file, 'w') as f:
            logging.info(f'Writing to state file {self.admin_state_file}, {admin}.')
            f.write(yaml.dump(admin))

    def get_admin_state(self):
        with open(self.admin_state_file) as f:
            admin = yaml.load(f.read(), Loader=yaml.Loader)
            return admin

    def write_admin_template(self):
        with open(self.admin_template) as f:
            admin = yaml.load(f.read(), Loader=yaml.Loader)
        
        with open(self.admin_state_file, 'w') as f:
            print(f'Writing template to state file {self.admin_state_file}, {admin}.')
            f.write(yaml.dump(admin))
