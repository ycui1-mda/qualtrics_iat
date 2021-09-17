import base64
import json
import streamlit as st
import qualtrics_tools
import iat_scorer
import script_generator
import web_utils

IATTask = script_generator.IATTask
SessionState = web_utils.SessionState
sidebar = st.sidebar
session_state = SessionState.get(
    templates=IATTask.templates(),
    working_task=None,
    iat_data=None,
    tool=qualtrics_tools.QualtricsTool()
)
tool = session_state.tool


def _set_width(width):
    st.markdown(
        f"""<style>.reportview-container .main .block-container{{max-width: {width}px;}}</style>""",
        unsafe_allow_html=True,
    )


def _preview_instructions(instruction, container):
    evaluated_instruction = eval(instruction)
    if isinstance(evaluated_instruction, list) and evaluated_instruction:
        for page_i, page in enumerate(evaluated_instruction, 1):
            container.markdown(f"__Page {page_i}__")
            container.markdown(page, unsafe_allow_html=True)
            container.markdown("___")


def create_downloadable_link(encoded, file_name, link_name, container, /, requires_encoding=True, filetype='txt'):
    if requires_encoding:
        encoded = encoded.encode()
    encoded_script = base64.b64encode(encoded).decode()
    href = f'<a href="data:file/{filetype};base64,{encoded_script}" ' \
           f'download="{file_name}">{link_name}</a>'
    container.markdown(href, unsafe_allow_html=True)


def _load_generator():
    sidebar.markdown("____")
    sidebar.header("Templates")

    templates = session_state.templates
    selected_template_name = sidebar.radio("Choose Template", IATTask.templates_names)
    selected_template_index = IATTask.templates_names.index(selected_template_name)
    if sidebar.button("Reload Selected Template"):
        templates[selected_template_index] = IATTask.reset_template(selected_template_name)
    working_task = session_state.working_task = templates[selected_template_index]
    sidebar.markdown(
        "Reloading template will overwrite your progress by resetting the configurations to the initial status."
    )

    sidebar.markdown("____")
    sidebar.header("Actions")
    sidebar.markdown("#### Generate Qualtrics File (QSF)")
    sidebar.markdown("Use this file to create a new survey. "
                     "If your Qualtrics subscription doesn't support this feature, "
                     "use the _Generate Script_ button below instead.")
    qsf_button = sidebar.button("Generate Template (QSF)")
    if qsf_button:
        template_js = working_task.generate_template_file()
        create_downloadable_link(
            template_js,
            "iat_qualtrics_template.qsf",
            "Download Qualtrics Template File",
            sidebar
        )

    sidebar.markdown("#### Generate JavaScript Script (JS)")
    sidebar.markdown("You'll build your survey yourself. The script will be added to the presentation question.")
    js_button = sidebar.button("Generate Script (JS)")
    if js_button:
        generated_script = working_task.generate_script()
        create_downloadable_link(
            generated_script,
            "iat_questionjs_script.js",
            "Download Question JS Code",
            sidebar
        )

    st.header("IAT Qualtrics Survey Generator")
    st.subheader("")
    st.subheader("Target Concepts")
    shared_stimuli_instruction = "(words or URLs to images), separated by commas. Enclose each word or URL with " \
                                 "single or double quotes and your entire list with square brackets for coding " \
                                 "purposes."
    target_positive_col, target_negative_col = st.beta_columns(2)

    working_task.target_positive_concept = target_positive_col.text_input(
        "Positive Target Concept",
        working_task.target_positive_concept
    )
    working_task.target_positive_stimuli = target_positive_col.text_area(
        f"Positive Target Stimuli {shared_stimuli_instruction}",
        working_task.target_positive_stimuli
    )
    working_task.target_negative_concept = target_negative_col.text_input(
        "Negative Target Concept",
        working_task.target_negative_concept
    )
    working_task.target_negative_stimuli = target_negative_col.text_area(
        f"Negative Target Stimuli {shared_stimuli_instruction}",
        working_task.target_negative_stimuli
    )

    stimulus_references = ["words", "pictures"]
    stimulus_medias = ["text", "image"]

    working_task.target_stimulus_reference = st.selectbox(
        "Target Stimuli Media (for references used in instructions)",
        stimulus_references,
        stimulus_references.index(working_task.target_stimulus_reference)
    )
    working_task.target_stimulus_media = st.selectbox(
        "Target Stimuli Media (for configuring web elements used in presentations). In some cases, for "
        "presentation consistency, words can be prepared as images.",
        stimulus_medias,
        stimulus_medias.index(working_task.target_stimulus_media)
    )

    st.subheader("Attribute Concepts")
    attribute_positive_col, attribute_negative_col = st.beta_columns(2)
    working_task.attribute_positive_concept = attribute_positive_col.text_input(
        "Positive Attribute Concept",
        working_task.attribute_positive_concept
    )
    working_task.attribute_positive_stimuli = attribute_positive_col.text_area(
        f"Positive Attribute Stimuli {shared_stimuli_instruction}",
        working_task.attribute_positive_stimuli
    )
    working_task.attribute_negative_concept = attribute_negative_col.text_input(
        "Negative Attribute Concept",
        working_task.attribute_negative_concept
    )
    working_task.attribute_negative_stimuli = attribute_negative_col.text_area(
        f"Negative Attribute Stimuli {shared_stimuli_instruction}",
        working_task.attribute_negative_stimuli
    )

    working_task.attribute_stimulus_reference = st.selectbox(
        "Attribute Stimuli Media (for references used in instructions)",
        stimulus_references,
        stimulus_references.index(working_task.attribute_stimulus_reference)
    )
    working_task.attribute_stimulus_media = st.selectbox(
        "Attribute Stimuli Media (for configuring web elements used in presentations). In some cases, for"
        "presentation consistency, words can be prepared as images.",
        stimulus_medias,
        stimulus_medias.index(working_task.attribute_stimulus_media)
    )
    st.markdown("____")

    st.header("Advanced Configurations")

    st.subheader("Study Name")
    working_task.study_name = st.text_input(
        "The study name will be useful if you have multiple IATs in one survey.",
        working_task.study_name
    )
    if working_task.study_name:
        st.markdown(
            f"The block responses will be saved as several embedded data with the name using the format: "
            f"{working_task.study_name}_block1Responses, {working_task.study_name}_block2Responses..."
            f"Setting the study name is necessary if you have multiple IAT experiments in a Qualtrics survey."
        )
    else:
        st.markdown(
            f"The block responses will be saved as several embedded data with the name using the format: "
            f"block1Responses, block2Responses..."
        )
    st.markdown("___")

    st.subheader("Switch Attributes or Targets for Block 5")
    switch_options = ["Attribute", "Target"]
    working_task.switch_attributes = st.selectbox(
        "Indicate whether you want to switch attributes or targets.",
        switch_options
    ) == switch_options[0]
    if working_task.switch_attributes:
        switch_text = "Block 5 will be the switched attributes opposite to Block 2."
    else:
        switch_text = "Block 5 will be the switched targets opposite to Block 1."
    st.markdown(switch_text)
    st.markdown("___")

    st.subheader("Estimated Duration")
    working_task.estimated_duration = st.text_input(
        "Estimated Duration for Completing Survey (please include the unit for the time)",
        working_task.estimated_duration
    )
    st.markdown(
        f"In the instruction, your subjects will be notified that it will take them about "
        f"{working_task.estimated_duration} for completing the study."
    )
    st.markdown("___")

    st.subheader("Counter-Balancing of Block Conditions")
    working_task.counter_balancing = st.checkbox("Enable Counter-Balancing", True)
    if working_task.counter_balancing:
        st.markdown("The order of congruency and left vs. right will be counter-balanced between subjects.")
    else:
        st.markdown("WARNING: The order of the blocks will be fixed for all subjects: congruent first "
                    "then incongruent.")
    st.markdown("___")

    st.subheader("Correction Requirement")
    working_task.requires_correction = st.checkbox(
        "Requires Correction After Making a Mistake",
        working_task.requires_correction
    )
    if working_task.requires_correction:
        st.markdown("Your task requires that the subject correct the error responses before it proceeds.")
        rt_options = {"After the first error response": "error", "After the correct response": "correct"}
        working_task.error_rt_option = rt_options[
            st.selectbox("How to Record Reaction Time for Error Responses", list(rt_options.keys()), 0)
        ]
        if working_task.error_rt_option == list(rt_options.values())[0]:
            st.markdown("For error responses, the reaction time will be recorded upon the first error attempt.")
        else:
            st.markdown("For error responses, the reaction time will be recorded upon the correct attempt.")
    else:
        working_task.auto_advance_delay = st.number_input("The delay in ms before the task proceeds "
                                                          "after a wrong responses", 300.0)
        st.markdown(f"Your task will automatically proceed {working_task.auto_advance_delay} ms after error responses.")
    st.markdown("___")

    st.subheader("Response Keys")
    st.markdown(
        "You can find the list of key codes from "
        "[Mozilla Website](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code/code_values)."
    )
    key_column_titles = ["Code (used for recording responses)", "Name (used for instructions)"]
    key_row_titles = ["Left Key", "Right Key", "Advance Key (to launch blocks)"]
    response_key_code_col, response_key_name_col = st.beta_columns(len(key_column_titles))
    response_key_code_col.markdown(f"__{key_column_titles[0]}__")
    response_key_name_col.write(f"__{key_column_titles[1]}__")
    working_task.left_key_code = response_key_code_col.text_input(
        key_row_titles[0],
        working_task.left_key_code,
        key=key_row_titles[0] + key_column_titles[0]
    )
    working_task.right_key_code = response_key_code_col.text_input(
        key_row_titles[1],
        working_task.right_key_code,
        key=key_row_titles[1] + key_column_titles[0]
    )
    working_task.advance_key_code = response_key_code_col.text_input(
        key_row_titles[2],
        working_task.advance_key_code,
        key=key_row_titles[2] + key_column_titles[0]
    )
    working_task.left_key_name = response_key_name_col.text_input(
        key_row_titles[0],
        working_task.left_key_name,
        key=key_row_titles[0] + key_column_titles[1]
    )
    working_task.right_key_name = response_key_name_col.text_input(
        key_row_titles[1],
        working_task.right_key_name,
        key=key_row_titles[1] + key_column_titles[1]
    )
    working_task.advance_key_name = response_key_name_col.text_input(
        key_row_titles[2],
        working_task.advance_key_name,
        key=key_row_titles[2] + key_column_titles[1]
    )
    st.markdown(
        f"When your task is completed on a desktop computer, the subject will use __{working_task.left_key_code}__ and "
        f"__{working_task.right_key_code}__, namely _{working_task.left_key_name}_ and "
        f"_{working_task.right_key_name}_ for "
        f"left and right responses. The __{working_task.advance_key_code}__ with "
        f"the name _{working_task.advance_key_name}_ "
        f"will be used to advance the task."
    )
    st.markdown("___")

    st.subheader("Overall Instruction")
    st.write("Instructions should be prepared as HTTP texts, and they will be rendered page by page. Each page will be "
             "a text string. Please use square brackets to wrap these individual pages, separated by commas. Previews "
             "are shown on the right side.")
    st.write("__Instruction for Desktop Users__")
    instruction_desktop_text_col, instruction_desktop_preview_col = st.beta_columns(2)
    working_task.overall_instruction_desktop = instruction_desktop_text_col.text_area(
        "HTTP Text",
        working_task.get_overall_instruction(False),
        key="overall_instruction_desktop",
        height=500
    )
    _preview_instructions(working_task.overall_instruction_desktop, instruction_desktop_preview_col)

    st.write("__Instruction for Mobile Users__")
    instruction_mobile_text_col, instruction_mobile_preview_col = st.beta_columns(2)
    working_task.overall_instruction_mobile = instruction_mobile_text_col.text_area(
        "HTTP Text",
        working_task.get_overall_instruction(True),
        key="overall_instruction_mobile",
        height=700
    )
    _preview_instructions(working_task.overall_instruction_mobile, instruction_mobile_preview_col)
    st.markdown("___")

    st.subheader("Display of Stimuli as Examples")
    working_task.shows_examples = st.checkbox("Shows Examples")
    if working_task.shows_examples:
        st.markdown(
            "Your subjects will review the stimuli to know what stimuli belong to what categories before they start "
            "the classification portion."
        )
        working_task.example_duration = st.number_input(
            "Example Duration in Milliseconds",
            working_task.example_duration
        )
        st.markdown("__Instructions Before Showing Examples__ (The rules for preparing the instructions are the "
                    "same as the ones for the overall instructions.)")
        example_instruction_text_col, example_instruction_preview_col = st.beta_columns(2)
        working_task.example_instruction = example_instruction_text_col.text_area(
            "HTTP Text",
            working_task.get_example_instruction(),
            key="example_instruction",
            height=600
        )
        _preview_instructions(working_task.example_instruction, example_instruction_preview_col)
    else:
        st.markdown(
            "Your subjects won't review the stimuli used in the study as examples before they start "
            "the classification portion."
        )
    st.markdown("___")

    st.subheader("Reminder Instructions")
    st.write("These instructions will be displayed right before the classification portion, as a friendly reminder.")
    st.write("__Reminder Instruction for Desktop Users__")
    reminder_instruction_desktop_text_col, reminder_instruction_desktop_preview_col = st.beta_columns(2)
    working_task.reminder_instruction_desktop = reminder_instruction_desktop_text_col.text_area(
        "HTTP Text",
        working_task.get_reminder_instruction(False),
        key="reminder_instruction_desktop",
        height=600
    )
    _preview_instructions(working_task.reminder_instruction_desktop, reminder_instruction_desktop_preview_col)

    st.write("__Reminder Instruction for Mobile Users__")
    reminder_instruction_mobile_text_col, reminder_instruction_mobile_preview_col = st.beta_columns(2)
    working_task.reminder_instruction_mobile = reminder_instruction_mobile_text_col.text_area(
        "HTTP Text",
        working_task.get_reminder_instruction(True),
        key="reminder_instruction_mobile",
        height=600
    )
    _preview_instructions(working_task.reminder_instruction_mobile, reminder_instruction_mobile_preview_col)
    st.markdown("___")

    st.subheader("Colors")
    color_column_titles = [
        "Attribute Word Stimulus Color",
        "Attribute Label Color",
        "Target Word Stimulus Color",
        "Target Label Color"
    ]
    color_columns = st.beta_columns(len(color_column_titles))
    working_task.attribute_word_color = color_columns[0].color_picker(
        color_column_titles[0],
        working_task.attribute_word_color
    )
    working_task.attribute_label_color = color_columns[1].color_picker(
        color_column_titles[1],
        working_task.attribute_label_color
    )
    working_task.target_word_color = color_columns[2].color_picker(
        color_column_titles[2],
        working_task.target_word_color
    )
    working_task.target_label_color = color_columns[3].color_picker(
        color_column_titles[3],
        working_task.target_label_color
    )
    st.markdown("___")

    st.subheader("Inter-Trial Interval (ITI)")
    working_task.inter_trial_interval = st.number_input(
        "ITI in Milliseconds",
        working_task.inter_trial_interval
    )
    st.markdown(f"Consecutive IAT trials will be separated by {working_task.inter_trial_interval} milliseconds.")
    st.markdown("___")

    st.subheader("Random Responses")
    working_task.prevent_random = st.checkbox("Prevent Random Responses", True)
    if working_task.prevent_random:
        working_task.minimum_allowed_reaction_time = st.number_input(
            "Minimum Allowed Reaction Time in Milliseconds",
            working_task.minimum_allowed_reaction_time
        )
        st.markdown(
            f"Responses shorter than {working_task.minimum_allowed_reaction_time} ms are considered random entries."
        )
        working_task.too_fast_response_error_message = st.text_input(
            "Warning Message for Random Responses",
            working_task.too_fast_response_error_message
        )
        st.markdown(
            f"When a random entry is identified, the screen will display: "
            f"{working_task.too_fast_response_error_message}"
        )
    else:
        st.markdown("The task won't detect whether subjects' responses are reasonably fast.")
    st.markdown("___")

    st.subheader("Minimum Preload Image Percent")
    working_task.minimum_preload_image_percent = st.slider(
        "The Percentage of Images Preloaded",
        min_value=0,
        max_value=100,
        value=working_task.minimum_preload_image_percent
    )
    st.markdown(
        "If your task uses images as stimuli, it's a good idea to preload images to increase the responsiveness of "
        "your task. If you don't want any preloading, set it to 0."
    )
    st.markdown("___")

    st.subheader("Inter-Trial Response Separator")
    working_task.inter_trial_response_separator = st.text_input(
        "The Delimiter",
        working_task.inter_trial_response_separator
    )
    st.markdown(
        f"Each block's responses will be saved as an embedded field in Qualtrics responses. In the block's "
        f"response, the trials' responses will be separated by {working_task.inter_trial_response_separator}. "
        f"Please don't use numbers or Y or N, which are part of the trial responses."
    )
    st.markdown("___")

    st.subheader("Block Specifications")
    st.write(
        "By default, the generator only works with the classic seven-block IAT. If you want to customize this "
        "behavior, you need to set the correct number of blocks, and specify the trial numbers and condition "
        "for each block."
    )
    working_task.block_trial_numbers = eval(st.text_input(
        "The number of trials for the blocks",
        working_task.block_trial_numbers
    ))
    st.markdown(
        f"The number of blocks for your task: {len(working_task.block_trial_numbers)}."
    )

    st.subheader("Automatic Testing")
    st.write(
        "When you specify a value that is greater than the minimally allowed response interval, "
        "the program can automatically enter the correct responses. When the value is "
        "smaller than or equal to the minimally allowed response interval, the program won't proceed by itself."
    )
    working_task.automatic_responses_delay = float(st.text_input(
        "Delay of automatic responses in milliseconds",
        working_task.automatic_responses_delay
    ))
    if working_task.automatic_responses_delay <= working_task.minimum_allowed_reaction_time:
        st.markdown(f"No automatic responses will be applied.")
    else:
        st.markdown(
            f"Automatic responses will be applied after the delay (ms): {working_task.automatic_responses_delay}"
        )


def _load_qualtrics_tools():
    sidebar.markdown("____")
    sidebar.header("Required API Configurations")
    sidebar.markdown(
        "To use the tools, you'll need to provide the necessary parameters in the first section. You can fetch "
        "these parameters from your Qualtrics account settings (Account Settings -> Qualtrics IDs). "
        "For more information about using these APIs, please "
        "refer to Qualtrics official website [Qualtrics API Quick Start]"
        "(https://api.qualtrics.com/instructions/docs/Instructions/Quick%20Start/qualtrics-api-quick-start.md)."
    )
    tool.api_token = sidebar.text_input("API Token", "")
    tool.data_center = sidebar.text_input("Data Center", "")
    tool.brand_center = sidebar.text_input("Brand Center", "")
    
    sidebar.markdown(
        "Your institute's designated Qualtrics website. For instance, MD Anderson Cancer Center uses "
        "'mdanderson.co1.qualtrics.com', in which case, you enter: mdanderson.co1 in the text field."
    )

    st.header("Qualtrics Tools")

    st.markdown("#### Upload Images to Qualtrics Graphics Library")
    st.markdown("Use this tool to upload images from your local computer to your Qualtrics Graphics Library.")
    upload_section = st.beta_expander("Upload Images")
    upload_section.markdown(
        "You can upload images from your computer. You can find the library ID # in your account settings "
        "(Account Settings -> Qualtrics IDs -> Libraries Table -> Row 1, the one starting with UR_)."
    )
    library_id = upload_section.text_input("Library ID #")
    qualtrics_folder = upload_section.text_input("Graphics Folder Name", "IAT Web App Upload")
    full_url = upload_section.checkbox("Generate Full URL", True)
    if full_url:
        url_note = "The full URLs for the images wil be generated. Please note that these images will be public, " \
                   "and anyone who has these URLs can access them."
    else:
        url_note = "Only the Qualtrics IDs of these images will be generated."
    upload_section.markdown(url_note)
    image_type = upload_section.selectbox("Image File Type", ['png', 'jpg', 'gif'])
    image_files = upload_section.file_uploader("Choose Images", ['png', 'jpg', 'gif'], True)
    upload_button = upload_section.button("Upload")
    if upload_button and image_files:
        image_urls = tool.upload_images_web(
            image_files,
            library_id,
            full_url,
            qualtrics_folder,
            image_type
        )
        upload_section.text_area("Image URLs", image_urls)
    st.markdown("____")

    st.markdown("#### Create Surveys")
    st.markdown("Use this tool to create surveys by setting JSON text or uploading QSF file.")
    create_section = st.beta_expander("Create Surveys")
    create_section.markdown(
        "You can create a survey either by specifying the template in a "
        "JSON format or by uploading the template file (.QSF). "
    )
    json_sources = ["Specify JSON Text", "Upload Qualtrics Survey File (.QSF)"]
    selected_json_source = create_section.selectbox("Required JSON Source", json_sources, 1)
    if selected_json_source == json_sources[0]:
        json_text = create_section.text_area("Enter the JSON Text")
        if json_text:
            json_text = json.loads(json_text)
    else:
        json_file = create_section.file_uploader("Choose Qualtrics Survey File", ['qsf'])
        if json_file:
            json_text = json.load(json_file)
    create_button = create_section.button("Create")
    if create_button and json_text:
        created_survey_id = tool.create_survey(json_text)
        created_survey_link = f"{tool.base_url}/Q/EditSection/Blocks?ContextSurveyID={created_survey_id}"
        create_section.markdown(f"Survey Link: [Qualtrics Survey (#{created_survey_id})]({created_survey_link})")
    st.markdown("____")

    st.markdown("#### Export Survey Responses")
    st.markdown("Use this tool to export survey responses for further processing.")
    export_section = st.beta_expander("Export Survey Responses")
    survey_id = export_section.text_input("Survey ID #")
    file_formats = ["csv", "tsv", "spss"]
    file_format = export_section.selectbox("File Format", file_formats)
    export_button = export_section.button("Export")
    if export_button:
        export_content = tool.export_responses(survey_id, file_format)
        create_downloadable_link(
            export_content,
            "survey_responses.zip",
            "Download survey_responses.zip",
            export_section,
            filetype="js",
            requires_encoding=False
        )
    st.markdown("____")

    st.markdown("#### Delete Images")
    st.markdown("Use this tool to delete images from your Qualtrics Graphics Library.")
    delete_section = st.beta_expander("Delete Images")
    delete_section.markdown("You can specify a list of either URLs or image ids.")
    delete_library_id = delete_section.text_input("Library ID #", key="for_deletion")
    delete_image_ids = delete_section.text_area("Image IDs")
    delete_button = delete_section.button("Delete")
    if delete_button and delete_image_ids:
        delete_image_ids = eval(delete_image_ids)
        if isinstance(delete_image_ids, list):
            delete_report = tool.delete_images(delete_library_id, delete_image_ids)
            delete_section.write(delete_report)
        else:
            delete_section.error("Please specify the list of image IDs.")
    st.markdown("____")

    st.markdown("#### Delete Survey")
    st.markdown("Use this tool to delete surveys from your Qualtrics Library.")
    delete_survey_section = st.beta_expander("Delete Survey")
    delete_survey_section.markdown("You can specify the survey id for deletion.")
    delete_survey_id = delete_survey_section.text_input("Survey ID")
    delete_confirm_text = st.text_input("Please enter Delete Survey to confirm your deletion.")
    delete_survey_button = delete_survey_section.button("Delete", key="delete_survey")
    if delete_survey_button and delete_survey_id and delete_confirm_text == "Delete Survey":
        delete_survey_report = tool.delete_survey(delete_survey_id)
        delete_survey_section.write(delete_survey_report)


def _load_scorer():
    sidebar.markdown("____")
    sidebar.header("Overview of Algorithms")
    sidebar.markdown(
        "__Algorithm Descriptions__ (Greenwald et al. Understanding and Using the Implicit Association Test: "
        "I. An Improved Scoring Algorithm. Journal of Personality and Social Psychology 2003 (85)2:192-216)"
    )
    sidebar.markdown("#### Conventional Algorithm")
    sidebar.markdown("1. Use data from B4 & B7 (counter-balanced order will be taken care of in the calculation).")
    sidebar.markdown(
        "2. Nonsystematic elimination of subjects for excessively slow responding and/or high error rates."
    )
    sidebar.markdown("3. Drop the first two trials of each block.")
    sidebar.markdown("4. Recode latencies outside 300/3,000 boundaries to the nearer boundary value.")
    sidebar.markdown("5. Log-transform the resulting values.")
    sidebar.markdown("6. Average the resulting values for each of the two blocks.")
    sidebar.markdown("7. Compute the difference: B7 - B4.")

    sidebar.markdown("#### Improved Algorithm")
    sidebar.markdown(
        "1. Use data from B3, B4, B6, & B7 (counter-balanced order will be taken care of in the calculation)."
    )
    sidebar.markdown(
        "2. Eliminate trials with latencies > 10,000 ms; Eliminate subjects for whom more than "
        "10% of trials have latency less than 300 ms."
    )
    sidebar.markdown("3. Use all trials; Delete trials with latencies below 400 ms (alternative).")
    sidebar.markdown(
        "4. Compute mean of correct latencies for each block. "
        "Compute SD of correct latencies for each block (alternative)."
    )
    sidebar.markdown(
        "5. Compute one pooled SD for all trials in B3 & B6, another for B4 & B7; Compute one pooled SD "
        "for correct trials in B3 & B6, another for B4 & B7 (alternative)."
    )
    sidebar.markdown(
        "6. Replace each error latency with block mean (computed in Step 5) + 600 ms; Replace each error "
        "latency with block mean + 2 x block SD of correct responses (alternative 1); "
        "Use latencies to correct responses when correction to error responses is required (alternative 2)."
    )
    sidebar.markdown("7. Average the resulting values for each of the four blocks.")
    sidebar.markdown("8. Compute two differences: B6 - B3 and B7 - B4.")
    sidebar.markdown("9. Divide each difference by its associated pooled-trials SD.")
    sidebar.markdown("10. Average the two quotients.")

    st.header("IAT Data Scorer")
    st.markdown("This scorer scores the data of the Qualtrics IAT survey in the CSV format.")
    data_file = st.file_uploader("IAT Data File", ["csv"])
    if data_file:
        session_state.iat_data = iat_scorer.IATData(data_file)
        session_state.iat_data.iat_data
        iat_data_clean = session_state.iat_data.clean_up()
        st.write(iat_data_clean)
        st.write(
            "Note: task (sin=single-label blocks, con=congruent blocks, inc=incongruent blocks. "
            "If you counter-balance the block order, it will be considered."
        )
        create_downloadable_link(
            iat_data_clean.to_csv(index=False),
            "IAT_Trial_Data.csv",
            "Download IAT Trial Data",
            st
        )
    iat_data = session_state.iat_data

    algorithms = ["Conventional Algorithm", "Improved Algorithm"]
    selected_algorithm_index = algorithms.index(st.selectbox("Choose Algorithm", algorithms, 1))
    calculation_params = dict()
    if selected_algorithm_index == 0:
        rt_cols = st.beta_columns(2)
        calculation_params['rt_low_cutoff'] = rt_cols[0].number_input(
            "Reaction Time (ms) Low Cutoff",
            value=300.0
        )
        calculation_params['rt_high_cutoff'] = rt_cols[1].number_input(
            "Reaction Time (ms) High Cutoff",
            value=3000.0
        )
        calculation_params['recode_outliers'] = st.checkbox(
            "Recode Outliers to Boundary Values",
            True
        )
        if calculation_params['recode_outliers']:
            st.write(
                f"Recode latencies outside "
                f"{calculation_params['rt_low_cutoff']}/{calculation_params['rt_high_cutoff']} "
                f"boundaries to the nearer boundary value."
            )
        else:
            st.write(
                f"Drop latencies outside "
                f"{calculation_params['rt_low_cutoff']}/{calculation_params['rt_high_cutoff']}"
            )
        calculation_params['trials_to_drop'] = st.number_input(
            "The Number of Trials to Drop for Each Block",
            value=2
        )
        st.write(f"The number of first trials to drop for each block: {calculation_params['trials_to_drop']}")
        calculation_params['allowed_error_rate'] = st.slider(
            "The Maximum Allowed Error Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0
        ) / 100.0
        st.write(f"Eliminate subjects whose error rate is higher than {calculation_params['allowed_error_rate']:.2%}.")
        calculation_params['allowed_rt_upper'] = st.number_input(
            "Slow Responding Cutoff",
            value=3000.0
        )
        st.write(f"Eliminate subjects whose mean reaction time is "
                 f"longer than {calculation_params['allowed_rt_upper']} ms.")
    else:
        calculation_params['rt_high_cutoff'] = st.number_input(
            "Reaction Time (ms) High Cutoff",
            value=10000.0
        )
        st.write(f"Eliminate trials with latencies > {calculation_params['rt_high_cutoff']} ms")
        rt_cols = st.beta_columns(2)
        calculation_params['rt_low_cutoff'] = rt_cols[0].number_input(
            "Reaction Time (ms) Low Cutoff",
            value=300.0
        )
        calculation_params['allowed_fast_rate'] = rt_cols[1].slider(
            "Exclusion cutoff for subjects with > x% of too fast responses (reaction time < low cutoff)",
            min_value=0.0,
            max_value=100.0,
            value=10.0
        ) / 100.0
        st.write(f"Eliminate subjects for who more than {calculation_params['allowed_fast_rate']:%} of the "
                 f"trials have less than {calculation_params['rt_low_cutoff']} ms")

        use_trials_cols = st.beta_columns(2)
        calculation_params['use_all_trials'] = use_trials_cols[0].checkbox("Use all trials", True)
        if calculation_params['use_all_trials']:
            st.write("Use all trials after the first two steps")
        else:
            calculation_params['rt_delete_cutoff'] = use_trials_cols[1].number_input(
                "Delete Trials Whose Latency is Below (ms)",
                value=400.0
            )
            st.write(f"Delete trials with latencies below {calculation_params['rt_delete_cutoff']} ms.")

        pooled_sd_options = ["All Trials", "Correct Trials Only"]
        calculation_params['pooled_sd_using_all'] = st.selectbox(
            "Calculation of Pooled SD",
            pooled_sd_options
        ) == pooled_sd_options[0]
        if calculation_params['pooled_sd_using_all']:
            st.write("Use all trials in B3 and B6 to calculate the pooled SD. Use all trials in B4 and B7 to "
                     "calculate the pooled SD.")
        else:
            st.write("Use only correct trials in B3 and B6 to calculate the pooled SD. Use only correct trials in "
                     "B4 and B7 to calculate the pooled SD.")

        replacement_options = [
            "Block mean of correct responses + punishment time in ms",
            "Block mean of correct responses + punishment time in block SD of correct responses",
            "Use latency to correct responses when correction is required after an error"
        ]
        calculation_params['replacement_option'] = replacement_options.index(
            st.selectbox("Replacement of error latencies", replacement_options)
        )
        if calculation_params['replacement_option'] == 0:
            calculation_params['rt_punishment'] = st.slider(
                "Reaction Time (ms) Punishment for Error Trials",
                value=600,
                min_value=0,
                max_value=2000
            )
            st.write(f"Replace each error latency with block mean (computed in Step 5) + "
                     f"{calculation_params['rt_punishment']} ms")
        elif calculation_params['replacement_option'] == 1:
            calculation_params['rt_punishment'] = st.slider(
                "Reaction Time (ms) Punishment for Error Trials",
                value=2,
                min_value=0,
                max_value=10
            )
            st.write(f"Replace each error latency with block mean (computed in Step 5) + "
                     f"{calculation_params['rt_punishment']} X block SD of correct responses")
        else:
            st.write("Use the reaction time to the correct response when a correction is required. "
                     "Please make sure that your experiment actually recorded the reaction time to the correct "
                     "response when an error is noted for a trial.")

    if st.button("Calculate"):
        if iat_data is None:
            st.error("Please upload your data first.")
            return
        algorithm_method = "improved" if selected_algorithm_index else "conventional"
        algorithm = iat_scorer.IATAlgorithm(algorithm_method, **calculation_params)
        scoring_summary, scored_iat_data = algorithm.process_data(iat_data)
        st.write("Scoring Parameters")
        st.code(algorithm)
        st.write("___")
        st.write("Scored Data Overall Summary")
        st.write(scoring_summary)
        create_downloadable_link(
            scoring_summary.to_csv(index=False),
            "IAT_Data_Scoring_Summary.csv",
            "Download IAT Scoring Summary",
            st
        )
        st.write("___")
        st.write("Scored Data by Response")
        st.write(scored_iat_data)
        create_downloadable_link(
            scored_iat_data.to_csv(index=False),
            "IAT_Data_Score.csv",
            "Download IAT Scores",
            st
        )


def _load_sidebar():
    sidebar.header("Tool List")
    app_tools = ["IAT Generator", "Qualtrics Tools", "IAT Data Scorer"]
    selected_tool = sidebar.radio("Choose Tool", app_tools, 0)
    if selected_tool == app_tools[0]:
        _load_generator()
    elif selected_tool == app_tools[1]:
        _load_qualtrics_tools()
    else:
        _load_scorer()


if __name__ == "__main__":
    _set_width(1200)
    _load_sidebar()
