import importlib.resources as pkg_resources
import json


class IATTask:
    """Data model to create the IAT task to run on Qualtrics
    
    Parameters
    -----------
    target_positive_concept: str, the positive target
    target_positive_stimuli: list[str], the list of positive target stimuli, words or links to images
    target_negative_concept: str, the negative target
    target_negative_stimuli: list[str], the list of negative target stimuli, words or links to images
    attribute_positive_concept: str, the positive attribute
    attribute_positive_stimuli: list[str], the list of positive attribute stimuli, words or links to images
    attribute_negative_concept: str, the negative attribute
    attribute_negative_stimuli: list[str], the list of negative attribute stimuli, words or links to images
    Refer to the __init__ for other parameters
    """
    templates_names = ["Custom Task", "Flower-Insect", "Gender-Career", "Mexican-US surname"]
    
    def __init__(self,
                 *,
                 target_positive_concept=None,
                 target_positive_stimuli=None,
                 target_negative_concept=None,
                 target_negative_stimuli=None,
                 attribute_positive_concept=None,
                 attribute_positive_stimuli=None,
                 attribute_negative_concept=None,
                 attribute_negative_stimuli=None,
                 **kwargs):
        """Initialization of the IATTask data model
        :param target_stimulus_reference: ["words", "pictures"], how to refer to target stimuli in the instruction
        :param target_stimulus_media: ["text", "image"], what media is used to present the target stimuli
        :param attribute_stimulus_reference: ["words", "pictures"], how to refer to attribute stimuli in the instruction
        :param attribute_stimulus_media: ["text", "image"], what media is used to present the attribute stimuli
        :param left_key_code: str, the key code for entering the left-side response
        :param left_key_name: str, how to refer to the left-side response in the instruction
        :param right_key_code: str, the key code for entering the right-side response
        :param right_key_name: str, how to refer to the right-side response in the instruction
        :param advance_key_code: str, the key code for advancing the task
        :param advance_key_name: str, how to refer to the advance key in the instruction
        :param requires_correction: bool, whether a correction is required when the response is wrong
        :param error_rt_option: ["error", "correct"], when a correction is required, how the reaction time is recorded,
            relative to the initial error trial or the correct trial
        :param auto_advance_delay: int, float, the delay after the incorrect response, it's only valid when a correction
            isn't required
        :param estimated_duration: str, the estimated duration for completing the task
        :param study_name: str, the name for the IAT task, it's required to be set when a survey has multiple IAT
            studies
        :param switch_attributes: bool, whether Block 5 switches attributes or targets
        :param counter_balancing: bool, whether the task should be counterbalanced between the target and attribute
            label pairings
        :param prevent_random: bool, whether you want to prevent random responses (too fast responses)
        :param minimum_allowed_reaction_time: int, float, when prevent_random is True, the minimum allowed reaction time
            below which, the response is considered random
        :param too_fast_response_error_message: str, the error message to be shown when a too fast response is found
        :param overall_instruction_desktop: list[str in the HTML format], the overall instruction for computer users
        :param overall_instruction_mobile: list[str in the HTML format], the overall instruction for mobile users
        :param reminder_instruction_desktop: list[str in the HTML format], the reminder instruction for computer users
        :param reminder_instruction_mobile: list[str in the HTML format], the reminder instruction for mobile users
        :param shows_examples: bool, whether to show the examples
        :param example_duration: int, float, how long each example will be shown, when shows_example is True
        :param example_instruction: list[str in the HTML format], the example instructions
        :param target_label_color: str, the color of the target labels
        :param target_word_color: str, the color of the target stimuli
        :param attribute_label_color: str, the color of the attribute labels
        :param attribute_word_color: str, the color of the attribute stimuli
        :param inter_trial_interval: int, float, the inter trial interval in milliseconds between trials
        :param minimum_preload_image_percent: int, float, the minimum percentage for the image preloading, it only
            applies when the stimuli are images
        :param inter_trial_response_separator: str, the separator between trial responses, which will be saved as
            embedded data fields by Qualtrics
        :param ending_message: str in the HTML format, the message to be shown after the task is over
        :param block_trial_numbers: list, the list of trial numbers for the seven blocks
        :param automatic_responses_delay: int, float, this is for testing purposes, when it's set to be >= the
            minimum_allowed_reaction_time, the automatic correct responses will be entered after the specified delay
        """
        self.target_positive_concept = target_positive_concept
        self.target_positive_stimuli = target_positive_stimuli
        self.target_negative_concept = target_negative_concept
        self.target_negative_stimuli = target_negative_stimuli
        self.attribute_positive_concept = attribute_positive_concept
        self.attribute_positive_stimuli = attribute_positive_stimuli
        self.attribute_negative_concept = attribute_negative_concept
        self.attribute_negative_stimuli = attribute_negative_stimuli
        
        self.target_stimulus_reference = kwargs.get("target_stimulus_reference", "words")
        self.target_stimulus_media = kwargs.get("target_stimulus_media", "text")
        self.attribute_stimulus_reference = kwargs.get("attribute_stimulus_reference", "words")
        self.attribute_stimulus_media = kwargs.get("attribute_stimulus_media", "text")
        
        self.left_key_code = kwargs.get("left_key_code", "KeyF")
        self.left_key_name = kwargs.get("left_key_name", "F")
        self.right_key_code = kwargs.get("right_key_code", "KeyJ")
        self.right_key_name = kwargs.get("right_key_name", "J")
        self.advance_key_code = kwargs.get("advance_key_code", "Space")
        self.advance_key_name = kwargs.get("advance_key_name", "Space")

        self.requires_correction = kwargs.get("requires_correction", True)
        self.error_rt_option = kwargs.get("error_rt_option", "error")
        self.auto_advance_delay = kwargs.get("auto_advance_delay", 300)
        self.estimated_duration = kwargs.get("estimated_duration", "5 minutes")
        self.study_name = kwargs.get("study_name", "")
        self.switch_attributes = kwargs.get("switch_attributes", True)
        self.counter_balancing = kwargs.get("counter_balancing", True)
        self.prevent_random = kwargs.get("prevent_random", True)
        self.minimum_allowed_reaction_time = kwargs.get("minimum_allowed_reaction_time", 250)
        self.too_fast_response_error_message = kwargs.get("too_fast_response_error_message",
                                                          "Too fast! Please choose your answer carefully.")
        
        self.overall_instruction_desktop = self.get_overall_instruction(mobile=False)
        self.overall_instruction_mobile = self.get_overall_instruction(mobile=True)
        self.reminder_instruction_desktop = self.get_reminder_instruction(mobile=False)
        self.reminder_instruction_mobile = self.get_reminder_instruction(mobile=True)
        self.shows_examples = kwargs.get("shows_examples", False)
        self.example_duration = kwargs.get("example_duration", 1500)
        self.example_instruction = self.get_example_instruction()

        self.target_label_color = kwargs.get("target_label_color", "#ffa500")
        self.target_word_color = kwargs.get("target_word_color", "#ffa500")
        self.attribute_label_color = kwargs.get("attribute_label_color", "#003B00")
        self.attribute_word_color = kwargs.get("attribute_word_color", "#003B00")
        
        self.inter_trial_interval = kwargs.get("inter_trial_interval", 250)
        self.minimum_preload_image_percent = kwargs.get("minimum_preload_image_percent", 50)
        self.inter_trial_response_separator = kwargs.get("inter_trial_response_separator", "_")
        self.ending_message = kwargs.get(
            "ending_message",
            "<p style='color: darkgreen'><br /><br />You have completed this task. "
            "<br /><br />"
            "Thank you for your time.<br /><br /></p>"
        )
        if self.ending_message is None:
            self.ending_message = "null"

        self.block_trial_numbers = kwargs.get(
            "block_trial_numbers",
            [20, 20, 20, 40, 20, 20, 40]
        )
        self.automatic_responses_delay = kwargs.get("automatic_responses_delay", 0)

    @staticmethod
    def custom_params(name):
        """Custom parameters for the IAT task with the specified name"""
        pleasant_words = "Joy Happy Laughter Love Friend Pleasure Peace Wonderful".split()
        unpleasant_words = "Evil Agony Awful Nasty Terrible Horrible Failure War".split()
        params = dict()
        if name == IATTask.templates_names[1]:
            params.update(
                target_positive_concept="Flower",
                target_positive_stimuli="Orchid Tulip Rose Daffodil Daisy Lilac Lily".split(),
                target_negative_concept="Insect",
                target_negative_stimuli="Wasp Flea Roach Centipede Moth Bedbug Gnat".split(),
                attribute_positive_concept="Pleasant",
                attribute_positive_stimuli=pleasant_words,
                attribute_negative_concept="Unpleasant",
                attribute_negative_stimuli=unpleasant_words,
                study_name="flower"
            )
        elif name == IATTask.templates_names[2]:
            params.update(
                target_positive_concept="Male",
                target_positive_stimuli="John Paul Mike Kevin Steve Greg Jeff Bill".split(),
                target_negative_concept="Women",
                target_negative_stimuli="Amy Joan Lisa Sarah Diana Kate Ann Donna".split(),
                attribute_positive_concept="Career",
                attribute_positive_stimuli="Executive Management Professional Corporation Salary Office "
                                           "Business Career".split(),
                attribute_negative_concept="Family",
                attribute_negative_stimuli="Home Parents Children Family Cousins Marriage Wedding Relatives".split(),
                study_name="gender"
            )
        elif name == IATTask.templates_names[3]:
            params.update(
                target_positive_concept="American",
                target_positive_stimuli="Smith Johnson Williams Brown Jones Miller Davis".split(),
                target_negative_concept="Mexican",
                target_negative_stimuli="Rodríguez Hernandez García Martínez González López Pérez".split(),
                attribute_positive_concept="Pleasant",
                attribute_positive_stimuli=pleasant_words,
                attribute_negative_concept="Unpleasant",
                attribute_negative_stimuli=unpleasant_words,
                study_name="surname"
            )
        return params

    @staticmethod
    def shared_params():
        """Create the shared parameters for the example IAT tasks"""
        return dict(
            target_stimulus_reference="words",
            target_stimulus_media="text",
            attribute_stimulus_reference="words",
            attribute_stimulus_media="text"
        )

    @staticmethod
    def reset_template(name):
        """Reset the template"""
        shared_kwargs = IATTask.shared_params()
        shared_kwargs.update(IATTask.custom_params(name))
        return IATTask(**shared_kwargs)

    @staticmethod
    def templates():
        """Create the template IAT tasks for the IAT web app"""
        shared_kwargs = IATTask.shared_params()
        templates_kwargs = list()
        for name in IATTask.templates_names:
            template_kwargs = shared_kwargs.copy()
            template_kwargs.update(IATTask.custom_params(name))
            templates_kwargs.append(template_kwargs)
        return [IATTask(**kwargs) for kwargs in templates_kwargs]

    def generate_script(self):
        """Create the script needed for the Qualtrics-IAT experiment"""
        task_stimulus_labels = {
            "p": self.target_positive_concept,
            "n": self.target_negative_concept,
            "+": self.attribute_positive_concept,
            "-": self.attribute_negative_concept
        }
        task_opposite_stimulus_labels = {
            "p": self.target_negative_concept,
            "n": self.target_positive_concept,
            "+": self.attribute_negative_concept,
            "-": self.attribute_positive_concept
        }
        task_attribute_stimulus_type = {
            "name": self.attribute_stimulus_reference,
            "media": self.attribute_stimulus_media
        }
        task_target_stimulus_type = {
            "name": self.target_stimulus_reference,
            "media": self.target_stimulus_media
        }
        task_stimulus_sources = f'{{"p": {self.target_positive_stimuli},' \
                                f'"n": {self.target_negative_stimuli},' \
                                f'"+": {self.attribute_positive_stimuli},' \
                                f'"-": {self.attribute_negative_stimuli}}}'
        task_left_key = {"code": self.left_key_code, "name": self.left_key_name}
        task_right_key = {"code": self.right_key_code, "name": self.right_key_name}
        task_advance_key = {"code": self.advance_key_code, "name": self.advance_key_name}

        task_setup = f"""let task = {{
    overallInstruction: {self.overall_instruction_desktop},
    mobileOverallInstruction: {self.overall_instruction_mobile},
    reminderInstruction: {self.reminder_instruction_desktop},
    mobileReminderInstruction: {self.reminder_instruction_mobile},
    endingMessage: {self.ending_message!r},
    stimulusLabels: {task_stimulus_labels!r},
    oppositeStimulusLabels: {task_opposite_stimulus_labels!r},
    stimulusSources: {task_stimulus_sources},
    attributeStimulusType: {task_attribute_stimulus_type!r},
    targetStimulusType: {task_target_stimulus_type!r},
    blockTrialNumbers: {self.block_trial_numbers},
    leftKey: {task_left_key},
    rightKey: {task_right_key},
    advanceKey: {task_advance_key},
    attributeLabelColor: {self.attribute_label_color!r},
    attributeWordColor: {self.attribute_word_color!r},
    targetLabelColor: {self.target_label_color!r},
    targetWordColor: {self.target_word_color!r},
    showExamples: {str(self.shows_examples).lower()},
    exampleDisplayTime: {self.example_duration},
    exampleInstruction: {self.example_instruction},
    interTrialInterval: {self.inter_trial_interval},
    minimumAllowedReactionTime: {self.minimum_allowed_reaction_time},
    minimumPreloadImagePercent: {self.minimum_preload_image_percent},
    interTrialResponseSeparator: {self.inter_trial_response_separator!r},
    requiresCorrection: {str(self.requires_correction).lower()},
    autoAdvanceDelay: {self.auto_advance_delay},
    tooFastResponseErrorMessage: {self.too_fast_response_error_message!r},
    blockConditions: [],
    studyName: {self.study_name!r},
    switchAttribute: {str(self.switch_attributes).lower()},
    counterBalancing: {str(self.counter_balancing).lower()},
    automaticResponsesDelay: {self.automatic_responses_delay}
}};"""
        standard_script = pkg_resources.read_text("templates", "iat_question_js_code.js")
        return task_setup + '\n' + standard_script

    def update_embedded_field(self, embedded_field, key):
        return self.study_name + "_" + embedded_field[key]

    def process_flow_item(self, flow_item, prefix):
        for embedded_field in flow_item["EmbeddedData"]:
            if ("Description" in embedded_field) and embedded_field["Description"].startswith(prefix):
                embedded_field["Description"] = self.update_embedded_field(embedded_field, "Description")
                embedded_field["Field"] = self.update_embedded_field(embedded_field, "Field")

    def generate_template_file(self):
        question_js = self.generate_script()
        json_template = json.loads(pkg_resources.read_text("templates", "iat_survey_template.qsf"))
        for item in filter(lambda x: x == "SurveyElements", json_template):
            for element in filter(lambda x: x["Element"] == "SQ", json_template[item]):
                element["Payload"]["QuestionJS"] = question_js
                break

            if not self.study_name:
                continue
            for element in filter(lambda x: x["Element"] == "FL", json_template[item]):
                for flow_item in filter(lambda x: x["Type"] == "EmbeddedData", element["Payload"]["Flow"]):
                    self.process_flow_item(flow_item, "block")

                for flow_item in filter(lambda x: x["Type"] == "BlockRandomizer", element["Payload"]["Flow"]):
                    for random_flow_item in flow_item["Flow"]:
                        self.process_flow_item(random_flow_item, "first")

        dumped_js = json.dumps(json_template)
        return dumped_js
    
    @staticmethod
    def _get_qsf_template():
        return pkg_resources.read_text("templates", "iat_survey_template.qsf")

    @property
    def _stimuli_types(self):
        _stimuli_types = self.attribute_stimulus_reference
        if self.attribute_stimulus_reference != self.target_stimulus_reference:
            _stimuli_types = _stimuli_types + " and " + self.target_stimulus_reference
        return _stimuli_types

    @property
    def _stimuli_types_singular(self):
        _stimuli_types_singular = self.attribute_stimulus_reference[:-1]
        if self.attribute_stimulus_reference != self.target_stimulus_reference:
            _stimuli_types_singular = _stimuli_types_singular + " or " + self.target_stimulus_reference[:-1]
        return _stimuli_types_singular

    def get_overall_instruction(self, mobile):
        paged_instruction = [
            f"<p>In this task, you will be presented with a set of {self._stimuli_types} to classify into groups."
            f"<br /><br />"
            f"The task requires that you classify the {self._stimuli_types} as quickly as you can "
            f"while making as few mistakes as possible."
            f"<br /><br />"
            f"This task takes about {self.estimated_duration}."
            f"<br /><br /></p>"
        ]
        if mobile:
            paged_instruction.extend([
                f"<div>In this task, you'll need to tap the touch screen to answer the questions.<br /><br />"
                f"When the {self._stimuli_types_singular} matches the label on the left side, "
                f"tap the <strong>left</strong> button.<br /><br />"
                f"When the {self._stimuli_types_singular} matches the label on the right side, "
                f"tap the <strong>right</strong> button.</div>",
                "If you're using a mobile device, please hold your device vertically and scroll "
                "the page to ensure that the entire box is visible on the screen."
                "<br /><br />"
                "Note: Don't pull down your page too fast, which may accidentally refresh the page and "
                "you'll lose your progress."
            ])
        else:
            paged_instruction.append(
                f"<div>In this task, you'll need to press {self.left_key_name} and {self.right_key_name} keys on "
                f"your keyboard to answer the questions.</div>"
                f"<div><br />When the {self._stimuli_types_singular} matches the label on the left side, press "
                f"<strong>{self.left_key_name}</strong> key.<br />"
                f"<br />When the {self._stimuli_types_singular} matches the label on the right side, press "
                f"<strong>{self.right_key_name}</strong> key.</div>"
            )
        return paged_instruction

    def get_example_instruction(self):
        return [
            f"<br /><br /><br />"
            f"<p>The following is the list of category labels for this study: "
            f"<strong>{self.target_positive_concept}</strong>, "
            f"<strong>{self.target_negative_concept}</strong>, "
            f"<strong>{self.attribute_positive_concept}</strong>, and "
            f"<strong>{self.attribute_negative_concept}</strong>.<br /><br />" 
            f"You will now see examples for each category. "
            f"The {self._stimuli_types} will be presented, with the categories shown at the top of the screen.",
            f"<br /><br /><br />"
            f"Each {self._stimuli_types_singular} will be shown briefly.<br /><br />"
            f"At this stage, you do not need to make any response.<br /><br />"
            f"Just look at the {self._stimuli_types_singular} carefully.</p>"
        ]

    def get_reminder_instruction(self, mobile):
        if mobile:
            response_element = "button"
            element0 = "Place your device on a desk such that you can tap the screen with your index fingers " \
                       "very quickly."
            element1 = "Position your device properly to enable fast response."
            element2 = f"Two buttons at the bottom will tell you which {self._stimuli_types} go with each button."
            displayed_left_key_name = "left"
            displayed_right_key_name = "right"
        else:
            response_element = "key"
            element0 = f"Place your left index finger on the {self.left_key_name} key " \
                       f"and your right index finger on the {self.right_key_name} key on your keyboard."
            element1 = f"Keep your index fingers on the <strong>{self.left_key_name} and " \
                       f"{self.right_key_name} keys</strong> to enable fast response."
            element2 = f"Two labels at the top will tell you which {self._stimuli_types} go with each key."
            displayed_left_key_name = self.left_key_name
            displayed_right_key_name = self.right_key_name
        if self.requires_correction:
            error_action = f"please correct your answer by pressing the other {response_element}"
        else:
            error_action = "please wait for the task to proceed by itself"
        return [
            f"<ul>"
            f"<li style='text-align: left;'>{element0}</li>"
            f"<li style='text-align: left;'>Press <strong>the {displayed_left_key_name} {response_element} "
            f"with your left "
            f"index finger</strong> if the {self._stimuli_types_singular} fits the category on the left.</li>"
            f"<li style='text-align: left;'>Press <strong>the {displayed_right_key_name} {response_element} "
            f"with your right "
            f"index finger</strong> if the {self._stimuli_types_singular} fits the category on the right.</li>"
            f"<li style='text-align: left;'>If you make a mistake, you will see an error message, "
            f"and {error_action}</li>"
            f"</ul>",
            f"<div style='text-align: center;'><strong>Keep in mind the following points</strong></div>"
            f"<ol>"
            f"<li style='text-align: left;'>{element1}</li>"
            f"<li style='text-align: left;'>{element2}</li>"
            f"<li style='text-align: left;'>Each {self._stimuli_types_singular} has a correct classification. "
            f"Most of these are easy.</li>"
            f"<li style='text-align: left;'>The test gives no results if you go slow. Please try to "
            f"<strong>go as fast as possible!</strong></li>"
            f"<li style='text-align: left;'><strong>Expect to make a few mistakes</strong> because of "
            f"going fast. That's OKAY!</li>"
            f"</ol>"
         ]
