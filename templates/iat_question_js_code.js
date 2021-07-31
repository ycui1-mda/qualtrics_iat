let boundingBox;
let boundingBoxAspectRatio;
let instructionElement;
let actionButton;
let warningElement;
let stimulusContainer;
let stimulusContainerPct = 95;
let heightRatio = 0.75;
let buttons;
let fixationElement;
let textElement;
let imageElement;
let errorElement;
let leftButtonElement;
let rightButtonElement;
let stimulusFlags = {};
let currentBlock = {
    condition: "",
    instruction: "",
    trials: [],
    loadedImages: new Set(),
    imageSources: new Set()
};
let currentTrial = {};
let currentTrialNumber = 0;
let currentBlockNumber = 0;
let exampleTrials = [];
let isMobile = false;
let pagedInstructions = null;
let pagedExampleInstructions = null;
let pagedReminderInstructions = null;


Qualtrics.SurveyEngine.addOnload(function()
{
    setBasicStyle(this);
    getDeviceInformation();
    randomizeBlockConditions();
    prepareStimuliFlags();
    createElements();
    addListeners();
    if (task.overallInstruction.length > 0) {
        showOverallInstruction();
    } else if (task.showExamples) {
        showExampleInstruction();
    } else if (task.reminderInstruction.length > 0) {
        showReminderInstruction();
    } else {
        launchBlock();
    }
});

function setBasicStyle(that) {
    that.hideNextButton();
    jQuery("#Plug").attr('style', 'display: none !important');
}

function getDeviceInformation() {
	let device = "${e://Field/device}";
	isMobile = /Android|webOS|iPhone|iPad|iPod/i.test(navigator.userAgent) || device === "mobile";
}

function properFontSize() {
    let fontSize;
    if (!isMobile) {
        fontSize = "24px";
    } else {
        if (screen.height > 1000) {
            fontSize = "22px";
        } else if (screen.height < 400) {
            fontSize = "12px";
        } else if (screen.height < 750) {
            fontSize = "14px";
        } else {
            fontSize = "18px";
        }
    }
    return fontSize;
}

function addListeners() {
    if (isMobile) {
        leftButtonElement.addEventListener("click", tapButton);
        rightButtonElement.addEventListener("click", tapButton);
    } else {
        window.addEventListener("keydown", enterResponse);
        window.focus();
    }
}

function randomizeBlockConditions() {
    if (!task.counterBalancing) {
        if (task.switchAttribute) {
            task.blockConditions = ["px", "x+", "p+", "p+", "x-", "p-", "p-"];
        } else {
            task.blockConditions = ["px", "x+", "p+", "p+", "nx", "n+", "n+"];
        }
    } else {
        let combinationFieldName = "firstCombination";
        if (task.studyName.length > 0) {
            combinationFieldName = task.studyName + "_firstCombination";
        }
        let firstCombination = Qualtrics.SurveyEngine.getEmbeddedData(combinationFieldName);
        console.log("First Combination", firstCombination);
        if (firstCombination) {
            generateBlockConditions(firstCombination);
        } else {
            const combinedConditions = ["p+", "p-", "n+", "n-"];
            const seedingCondition = combinedConditions[Date.now() % combinedConditions.length];
            generateBlockConditions(seedingCondition);
        }
    }
    let conditionFieldName = "blockConditions"
    if (task.studyName.length > 0) {
        conditionFieldName = task.studyName + "_blockConditions";
    }
    Qualtrics.SurveyEngine.setEmbeddedData(
        conditionFieldName,
        task.blockConditions.join("|")
    );
}

function generateBlockConditions(seedingCondition) {
    const oppositeConditionMapping = {"p": "n", "n": "p", "+": "-", "-": "+"};
    const conditionBlock1 = seedingCondition[0] + "x";
    const conditionBlock2 = "x" + seedingCondition[1];
    const conditionBlock34 = seedingCondition;
    let conditionBlock5, conditionBlock67;
    if (task.switchAttribute) {
        conditionBlock5 = "x" + oppositeConditionMapping[seedingCondition[1]];
        conditionBlock67 = seedingCondition[0] + conditionBlock5[1];
    } else {
        conditionBlock5 = oppositeConditionMapping[seedingCondition[0]] + "x";
        conditionBlock67 = conditionBlock5[0] + seedingCondition[1];
    }
    task.blockConditions = [
        conditionBlock1,
        conditionBlock2,
        conditionBlock34,
        conditionBlock34,
        conditionBlock5,
        conditionBlock67,
        conditionBlock67
    ];
    console.log("task.blockConditions");
    console.log(task.blockConditions);
}

function prepareStimuliFlags() {
    Object.entries(task.stimulusSources).forEach(([flag, stimuli]) => {
        stimuli.forEach(stimulus => {
            stimulusFlags[stimulus] = flag;
        });
    });
}

function createElements() {
    let stimulusStyle = [
        "position: absolute",
        "top: 0",
        "left: 0",
        "bottom: 0",
        "right: 0",
        "text-align: center",
        "vertical-align: middle",
        "font-size: 40px",
        "background-color: transparent",
        "color: black",
        "display: flex",
        "justify-content: center",
        "align-items: center",
        "overflow: hidden",
        "max-height: 90%",
        "max-width: 90%",
        "margin: auto"
    ];
    boundingBox = document.getElementsByClassName("QuestionBody")[0];
    if (isMobile) {
        boundingBox.style.width = "100%";
        // let boundingBoxHeightPct = Math.max((screen.height / screen.width * 100 - 30), 133);
        // let boundingBoxHeightPct = Math.max((screen.height / screen.width * 100 - 30), 133);
        boundingBoxAspectRatio = screen.height / screen.width
        boundingBox.style.paddingTop = (boundingBoxAspectRatio * heightRatio * 100).toString() + "%";
        boundingBox.style.border = "3px solid gray";
        stimulusContainer = addStimulusContainer();
        addStimulusElements(stimulusContainer, stimulusStyle);
        addFixation(stimulusContainer, stimulusStyle);
        addButtonsForMobile();
        addErrorWarning(stimulusContainer);
    } else {
        boundingBox.setAttribute("style", "width: 900px; height: 600px; border: 3px solid gray");
        addStimulusElements(boundingBox, stimulusStyle);
        addFixation(boundingBox, stimulusStyle);
        addButtonsForDesktop();
        addErrorWarning(boundingBox);
    }
    boundingBox.style.backgroundColor = "lightgray";
    instructionElement = addInstructionElement();
    actionButton = addActionButtonElement();
    hideTaskElements();
}

function hideTaskElements() {
    updateElementsVisibility([
        [textElement, "none"],
        [imageElement, "none"],
        [fixationElement, "none"],
        [instructionElement, "none"],
        [actionButton, "none"],
        [errorElement, "none"],
        [buttons, "none"],
        [stimulusContainer, "none"]
    ]);
}

function addButtonsForMobile() {
    buttons = document.createElement("div");
    buttons.setAttribute("style",
            "position: absolute; text-align: center; " +
        "width: 95%; bottom: 0%; left: 2.5%; right: 2.5%");
    // const screenRatio = Math.max(screen.height, screen.width) / Math.min(screen.height, screen.width);
    // buttons.style.paddingTop = Math.min(70, Math.floor((screenRatio - 1) * 100 - 5)).toString() + "%";
    // buttons.style.top = ((boundingBoxAspectRatio - 1) * 100).toString() + "%";
    buttons.style.top = (stimulusContainerPct / (boundingBoxAspectRatio * heightRatio)).toString() + "%";
    // console.log("stimulusContainerPct:", stimulusContainerPct);
    // console.log("boundingBoxAspectRatio:", boundingBoxAspectRatio);
    // console.log("buttons.style.top:", buttons.style.top);
    boundingBox.appendChild(buttons);
    leftButtonElement = addButtonElementForMobile("left", buttons);
    rightButtonElement = addButtonElementForMobile("right", buttons);
}

function addButtonsForDesktop() {
    buttons = document.createElement("div");
    buttons.setAttribute("style",
        "position: absolute; top: 2.5%; left: 0%; right: 0%;");
    boundingBox.appendChild(buttons);
    leftButtonElement = addCategoryLabel("left", buttons);
    rightButtonElement = addCategoryLabel("right", buttons);
}

function addCategoryLabel(side, container) {
    let sharedButtonStyle = [
        "position: absolute",
        "top: 0%",
        "width: 20%"
    ];
    let button = document.createElement("div");
    button.id = "iat_" + side + "_button";
    sharedButtonStyle.push(side + ": 2.5%");
    button.setAttribute("style", sharedButtonStyle.join("; "));
    button.style.fontSize = properFontSize();
    container.appendChild(button);
    return button;
}

function addButtonElementForMobile(side, buttons) {
    let buttonStyle = [
        "border: 3px solid darkgray",
        "border-radius: 2px",
        "margin: 2.5%",
        "position: absolute",
        "width: 45%",
        "height: 100%",
        "white-space: normal",
        "bottom: 0",
        "display: table-cell",
        "outline: none",
        "max-height: 200px"
    ]
    let button = document.createElement("button");
    button.id = "iat_" + side + "_button";
    buttonStyle.push(side + ": 0%");
    button.setAttribute("style", buttonStyle.join("; "));
    button.style.fontSize = properFontSize();
    buttons.appendChild(button);
    return button;
}

function  addStimulusContainer() {
    let stimulusContainerStyle = [
        "background-color: transparent",
        "position: absolute",
        "width: 95%",
        "padding-top: 95%",
        // "border: 3px solid black",
        "top: 0%",
        "left: 2.5%",
        "right: 2.5%"
    ];
    let stimulusContainer = document.createElement("div");
    stimulusContainer.setAttribute("style", stimulusContainerStyle.join("; "));
    boundingBox.appendChild(stimulusContainer);
    let hWRatio = screen.height / screen.width;
    if ((screen.height > 1000 && hWRatio < 1.55) || hWRatio < 1.34) {
        stimulusContainer.style.paddingTop = "80%";
        stimulusContainerPct = 80;
    }
    return stimulusContainer
}

function addErrorWarning(container) {
    errorElement = document.createElement("p");
    errorElement.setAttribute("style",
        "position: absolute; text-align: center; bottom: 0%; color: red; font-size: 32px; left: 0; right: 0");
    errorElement.appendChild(document.createTextNode("X"));
    container.appendChild(errorElement);
}

function addFixation(container, stimulusStyle) {
    fixationElement = document.createElement("p")
    fixationElement.setAttribute("style", stimulusStyle.join("; "));
    fixationElement.appendChild(document.createTextNode("+"));
    container.appendChild(fixationElement);
}

function addStimulusElements(container, stimulusStyle) {
    const medias = [task.attributeStimulusType["media"], task.targetStimulusType["media"]];
    if (medias.includes("text")) {
        textElement = document.createElement("p");
        textElement.appendChild(document.createTextNode(""));
        textElement.setAttribute("style", stimulusStyle.join("; "));
        textElement.style.fontSize = "30px";
        container.appendChild(textElement);
    }
    if (medias.includes("image")) {
        imageElement = document.createElement("img");
        imageElement.setAttribute("style", stimulusStyle.join("; "));
        container.appendChild(imageElement);
    }
}

function showReminderInstruction() {
    if (!pagedReminderInstructions) {
        pagedReminderInstructions =
            isMobile ? task.mobileReminderInstruction:task.reminderInstruction;
        toggleInstructionElements("block");
        updateElementsVisibility([
            [imageElement, "none"],
            [textElement, "none"],
            [stimulusContainer, "none"]
        ]);
    }
    actionButton.id = "iat_classification_instruction";
    let nextPage = pagedReminderInstructions.shift();
    if (nextPage) {
        instructionElement.innerHTML = nextPage;
    } else {
        toggleInstructionElements("none");
        launchBlock();
    }
}

function launchBlock() {
    updateElementsVisibility([
        [textElement, "none"],
        [imageElement, "none"],
        [fixationElement, "none"]
    ]);
    if (currentBlockNumber >= 1 && currentBlockNumber <= task.blockConditions.length) {
        saveBlockResponses();
    }
    currentBlockNumber++;
    if (isMobile) {
        boundingBox.style.border = "3px solid white";
        stimulusContainer.style.border = "3px solid black";
    }
    // console.log("Launching Block", currentBlockNumber);
    if (currentBlockNumber <= task.blockConditions.length) {
        currentTrialNumber = 0;
        currentBlock.imageSources = new Set();
        currentBlock.loadedImages = new Set();
        currentBlock.condition = task.blockConditions[currentBlockNumber - 1];
        generateBlockInstruction();
        generateBlockTrials();
        preloadTrials();
        showBlockInstruction();
        document.body.style.cursor = 'none';
    } else {
        document.body.style.cursor = 'unset';
        showEndingMessage();
    }
}

function showOverallInstruction() {
    if (!pagedInstructions) {
        pagedInstructions = isMobile ? task.mobileOverallInstruction:task.overallInstruction;
        toggleInstructionElements("block");
    }
    actionButton.id = "iat_overall_instruction";
    let nextPage = pagedInstructions.shift();
    if (nextPage) {
        instructionElement.innerHTML = nextPage;
    } else {
        if (task.showExamples) {
            showExampleInstruction();
        } else if (task.reminderInstruction.length > 0) {
            showReminderInstruction();
        } else {
            toggleInstructionElements("none");
            launchBlock();
        }
    }
}

function executeAction(event) {
    let element = event.target;
    if (element.id === "iat_overall_instruction") {
        showOverallInstruction();
    } else if (element.id === "iat_example_instruction") {
        showExampleInstruction();
    } else if (element.id === "iat_classification_instruction") {
        showReminderInstruction();
    }
}

function addInstructionElement() {
    let instructionElement = document.createElement("div");
    instructionElement.id = "iat_instruction";
    instructionElement.setAttribute("style",
        "text-align: center; top: 5%; left: 2.5%; right: 2.5%; position: absolute; color: black");
    instructionElement.style.fontSize = properFontSize();
    boundingBox.appendChild(instructionElement);
    return instructionElement;
}

function addActionButtonElement() {
    let actionButtonElement = document.createElement("button");
    actionButtonElement.addEventListener("click", executeAction);
    actionButtonElement.setAttribute("style",
        "background-color: green; border: none; padding: 8px 16px; " +
        "color: white; text-align: center; display: block; margin: 0 auto; " +
        "position: absolute; left: 20%; right: 20%; bottom: 2.5%; outline: none;");
    actionButtonElement.style.fontSize = properFontSize();
    actionButtonElement.textContent = "Continue";
    boundingBox.appendChild(actionButtonElement);
    return actionButtonElement;
}

function toggleInstructionElements(display) {
    updateElementsVisibility([
        [instructionElement, display],
        [actionButton, display]
    ]);
}

function showExampleInstruction() {
    if (!pagedExampleInstructions) {
        pagedExampleInstructions = task.exampleInstruction;
        toggleInstructionElements("block");
        prepareExamples();
    }
    actionButton.id = "iat_example_instruction";
    let nextPage = pagedExampleInstructions.shift();
    // console.log("What's next page?", nextPage);
    if (nextPage) {
        instructionElement.innerHTML = nextPage;
    } else {
        startShowingExamples();
    }
}

function prepareExamples() {
    Object.entries(task.stimulusSources).forEach(([flag, stimuli]) => {
        let shuffledStimuli = stimuli.slice();
        shuffleArray(shuffledStimuli);
        shuffledStimuli.forEach(stimulus => {
            stimulusFlags[stimulus] = flag;
            exampleTrials.push({
                sourceStimulus: stimulus,
                sourceFlag: flag,
                sourceMedia: ["p", "n"].includes(flag) ? task.targetStimulusType["media"]:task.attributeStimulusType["media"],
                isAttribute: ["+", "-"].includes(flag)
            });
        });
    });
}


function startShowingExamples() {
    // console.log("startShowingExamples");
    toggleInstructionElements("none");
    loadNextExample();
}

function loadNextExample() {
    if (isMobile) {
        updateElementsVisibility([[stimulusContainer, "block"]]);
    }
    let exampleCategoryLabel = document.getElementById("iat_example_label");
    if (!exampleCategoryLabel) {
        exampleCategoryLabel = document.createElement("div");
        exampleCategoryLabel.id = "iat_example_label";
        exampleCategoryLabel.setAttribute("style",
            "text-align: center; position: absolute; top: 2.5%; left: 0; right: 0; color: black");
        exampleCategoryLabel.style.fontSize = properFontSize()
        // exampleCategoryLabel.style.margin = isMobile ? "0%":"2.5%";
        // if (isMobile) {
        //     stimulusContainer.appendChild(exampleCategoryLabel);
        // } else {
        //
        // }
        boundingBox.appendChild(exampleCategoryLabel);
    }
    let exampleTrial = exampleTrials.pop();
    if (exampleTrial) {
        exampleCategoryLabel.textContent = task.stimulusLabels[exampleTrial.sourceFlag];
        if (exampleTrial.sourceMedia === "image") {
            imageElement.src = exampleTrial.sourceStimulus;
            updateElementsVisibility([
                [imageElement, "flex"],
                [textElement, "none"]
            ]);
        } else {
            textElement.style.color = exampleTrial.isAttribute ? task.attributeWordColor:task.targetWordColor;
            exampleCategoryLabel.style.color = textElement.style.color;
            const textNode = textElement.childNodes[0];
            textNode.nodeValue = exampleTrial.sourceStimulus;
            updateElementsVisibility([
                [imageElement, "none"],
                [textElement, "flex"]
            ]);
        }
        setTimeout(loadNextExample, task.exampleDisplayTime);
    } else {
        exampleCategoryLabel.remove();
        if (task.reminderInstruction.length > 0) {
            showReminderInstruction();
        } else {
            launchBlock();
        }
    }
}

function generateBlockTrials() {
    currentBlock.trials = [];
    const blockTrialNumber = task.blockTrialNumbers[currentBlockNumber - 1];
    for (let i = 0; i < blockTrialNumber; i++) {
        currentBlock.trials.push({
            stimulus: null,
            flag: null,
            media: null,
            correct: null,
            isAttribute: false,
            startTime: null,
            reactionTime: null
        });
    }
    let singleBlock = currentBlock.condition.includes("x");
    if (singleBlock) {
        updateSingleBlockTrials("+-".includes(currentBlock.condition[1]));
    } else {
        updateCombinedBlockTrials();
    }
}

function attributeStimuli() {
    const stimuli =  task.stimulusSources['+'].concat(task.stimulusSources['-']);
    shuffleArray(stimuli);
    return stimuli;
}

function targetStimuli() {
    const stimuli = task.stimulusSources['p'].concat(task.stimulusSources['n']);
    shuffleArray(stimuli);
    return stimuli;
}

function updateSingleBlockTrials(forAttributeBlock) {
    const blockTrialNumber = currentBlock.trials.length;
    let updatedTrialNumber = 0;
    let media = forAttributeBlock ? task.attributeStimulusType["media"]:task.targetStimulusType["media"];
    let sources = [];
    while (updatedTrialNumber < blockTrialNumber) {
        let trial = currentBlock.trials[updatedTrialNumber];
        if (sources.length < 1) {
            sources = forAttributeBlock ? attributeStimuli():targetStimuli();
        }
        trial.stimulus = sources.pop();
        trial.flag = stimulusFlags[trial.stimulus];
        trial.media = media;
        trial.isAttribute = forAttributeBlock;
        if (trial.media === "image") {
            currentBlock.imageSources.add(trial.stimulus);
        }
        updatedTrialNumber++;
    }
}

function updateCombinedBlockTrials() {
    const blockTrialNumber = currentBlock.trials.length;
    let updatedTrialNumber = 0;
    let sources = [attributeStimuli(), targetStimuli()];
    let sourceNumber = Date.now() % 2;
    while (updatedTrialNumber < blockTrialNumber) {
        let trial = currentBlock.trials[updatedTrialNumber];
        if (sources[sourceNumber].length < 1) {
            sources[sourceNumber] = sourceNumber === 0 ? attributeStimuli():targetStimuli()
        }
        trial.stimulus = sources[sourceNumber].pop();
        trial.flag = stimulusFlags[trial.stimulus];
        trial.media = sourceNumber === 0 ? task.attributeStimulusType["media"]:task.targetStimulusType["media"];
        trial.isAttribute = sourceNumber === 0;
        if (trial.media === "image") {
            currentBlock.imageSources.add(trial.stimulus);
        }
        sourceNumber = 1 - sourceNumber;
        updatedTrialNumber++;
    }
}

function preloadTrials() {
    if (currentBlock.imageSources.size > 0) {
        for (let i = 0; i < currentBlock.trials.length; i++) {
            const trial = currentBlock.trials[i];
            if (trial.media === "image") {
                const image = new Image();
                image.src = trial.stimulus;
                image.onload = function () {
                    currentBlock.loadedImages.add(trial.stimulus);
                }
            }
        }
    }
}

function beginBlock() {
    // console.log("currentBlock.imageSources:", currentBlock.imageSources);
    // console.log("currentBlock.loadedImages:", currentBlock.loadedImages);
    if (currentBlock.imageSources.size > 0 &&
        currentBlock.loadedImages.size < currentBlock.imageSources.size * task.minimumPreloadImagePercent / 100) {
        showWarningMessage("Some stimuli are still being downloaded. Please try again later. If the problem" +
            "persists, please notify the research team.");
        return;
    }
    updateElementsVisibility([
        [instructionElement, "none"],
        [stimulusContainer, "block"]
    ]);
    loadNextTrial();
}

function loadNextTrial() {
    dismissErrorMessage();
    currentTrialNumber++;
    if (currentTrialNumber <= currentBlock.trials.length) {
        updateElementsVisibility([
            [fixationElement, "flex"],
            [textElement, "none"],
            [imageElement, "none"]
        ]);
        setTimeout(loadStimulus, task.interTrialInterval);
    } else {
       launchBlock();
    }
}

function updateElementsVisibility(elementDisplays) {
    for (let i = 0; i < elementDisplays.length; i++) {
        const elementDisplay = elementDisplays[i];
        const element = elementDisplay[0];
        const display = elementDisplay[1];
        if (element) {
            element.style.display = display;
        }
    }
}

function loadStimulus() {
    currentTrial = currentBlock.trials[currentTrialNumber - 1];
    let elementsDisplays = [];
    if (currentTrial.media === "image") {
        imageElement.src = currentTrial.stimulus;
        elementsDisplays.push([imageElement, "flex"]);
    } else {
        textElement.style.color = currentTrial.isAttribute ? task.attributeWordColor:task.targetWordColor;
        const textNode = textElement.childNodes[0];
        textNode.nodeValue = currentTrial.stimulus;
        elementsDisplays.push([textElement, "flex"]);
    }
    elementsDisplays.push([fixationElement, "none"]);
    updateElementsVisibility(elementsDisplays);
    currentTrial.startTime = Date.now();
    // console.log("loading next trial", currentTrial);
    // console.log("Correct Side: ", currentBlock.condition.includes(currentTrial.flag) ? "F":"J");
    if (task.automaticResponsesDelay > task.minimumAllowedReactionTime) {
        setTimeout(applyAutomaticResponses, automaticResponsesDelay);
    }
}

function applyAutomaticResponses() {
    let correctSide = currentBlock.condition.includes(currentTrial.flag) ? "l":"r";
    scoreResponse(correctSide)
}

function tapButton(event) {
    if (currentTrialNumber < 1) {
        beginBlock();
    } else {
        let targetElement = event.target;
        if (!targetElement.id) {
            targetElement = targetElement.parentElement;
        }
        let side = targetElement.id["iat_".length];
        scoreResponse(side);
    }
}

function enterResponse(event) {
    event.preventDefault();
    if (currentBlockNumber < 1) {
        return;
    }
    if (currentTrialNumber < 1) {
        if (task.advanceKey['code'] === event.code) {
            beginBlock();
        }
    } else {
        if ([task.leftKey["code"], task.rightKey["code"]].includes(event.code)) {
            scoreResponse(task.leftKey["code"] === event.code ? "l":"r");
        } else {
            showWarningMessage("The key isn't allowed for the task.");
        }
    }
}

function scoreResponse(side) {
    // don't score response during the ITI
    if (!currentTrial || !currentTrial.startTime) {
        // console.log("Next trial is not set yet: ", currentTrial);
        return;
    }
    // console.log("Pressed side: ", side);
    // if response is set for the current trial and task doesn't require correction, skip scoring
    if (currentTrial.correct !== null && !task.requiresCorrection) {
        return;
    }
    let reactionTime = Date.now() - currentTrial.startTime;
    // prevent subjects from randomly answering the questions
    if (reactionTime < task.minimumAllowedReactionTime) {
        // console.log("Too fast, please slow down");
        showWarningMessage(task.tooFastResponseErrorMessage);
        return;
    }
    // set the reaction time only when a response hasn't been recorded
    if (!currentTrial.reactionTime) {
        currentTrial.reactionTime = reactionTime;
    }
    const correctSide = currentBlock.condition.includes(currentTrial.flag) ? "l":"r";
    if (side === correctSide) {
        if (currentTrial.correct === null) {
            currentTrial.correct = true;
        }
        // console.log("After scoring response correct: ", currentTrial);
        currentTrial = null;
        loadNextTrial();
    } else {
        currentTrial.correct = false;
        // console.log("After scoring response incorrect: ", currentTrial);
        updateElementsVisibility([[errorElement, "block"]]);
        if (!task.requiresCorrection) {
            currentTrial = null;
            setTimeout(loadNextTrial, task.autoAdvanceDelay);
        }
    }
}

function saveBlockResponses() {
    let blockResponses = [];
    let blockTrials = [];
    for (let i = 0; i < currentBlock.trials.length; i++) {
        let trial = currentBlock.trials[i];
        blockResponses.push([(i + 1).toString(), trial.correct ? "Y":"N", trial.reactionTime].join(""));
        blockTrials.push(trial.stimulus);
    }
    // console.log("Block Responses:", blockResponses);
    var responsePrefix = "block";
    if (task.studyName.length > 0) {
        responsePrefix = task.studyName + "_block";
    }
    Qualtrics.SurveyEngine.setEmbeddedData(
        responsePrefix + currentBlockNumber.toString() + "Responses",
        blockResponses.join(task.interTrialResponseSeparator)
    );
    Qualtrics.SurveyEngine.setEmbeddedData(
        responsePrefix + currentBlockNumber.toString() + "Trials",
        blockTrials.toString()
    );
}

function showBlockInstruction() {
    if (isMobile) {
        updateElementsVisibility([
            [buttons, "block"],
            [stimulusContainer, "none"],
            [instructionElement, "block"],
            [actionButton, "none"]
        ]);
    } else {
        updateElementsVisibility([
            [buttons, "block"],
            [instructionElement, "block"],
            [actionButton, "none"],
            [textElement, "none"],
            [imageElement, "none"]
        ]);
    }
    instructionElement.innerHTML = currentBlock.instruction;
}

function generateBlockInstruction() {
    let leftButtonText, leftLabelText, rightButtonText, rightLabelText;
    let targetCondition = currentBlock.condition[0];
    let attributeCondition = currentBlock.condition[1];
    if ((attributeCondition !== "x" && targetCondition !== "x")) {
        leftLabelText = task.stimulusLabels[targetCondition] + " " + task.targetStimulusType["name"]  + " or " +
            task.stimulusLabels[attributeCondition] + " " + task.attributeStimulusType["name"];
        rightLabelText = task.oppositeStimulusLabels[targetCondition] + " " + task.targetStimulusType["name"] + " or " +
            task.oppositeStimulusLabels[attributeCondition] + " " + task.attributeStimulusType["name"];
        updateCombinedLabelText(leftButtonElement, task.stimulusLabels[attributeCondition], task.stimulusLabels[targetCondition]);
        updateCombinedLabelText(rightButtonElement, task.oppositeStimulusLabels[attributeCondition], task.oppositeStimulusLabels[targetCondition]);
    } else {
        let forAttribute = attributeCondition !== "x";
        if (attributeCondition !== "x" && targetCondition === "x") {
            leftButtonText = task.stimulusLabels[attributeCondition];
            rightButtonText = task.oppositeStimulusLabels[attributeCondition];
            leftLabelText = leftButtonText + " " + task.attributeStimulusType["name"];
            rightLabelText = rightButtonText + " " + task.attributeStimulusType["name"];
        } else if (attributeCondition === "x" && targetCondition !== "x") {
            leftButtonText = task.stimulusLabels[targetCondition];
            rightButtonText = task.oppositeStimulusLabels[targetCondition];
            leftLabelText = leftButtonText + " " + task.targetStimulusType["name"];
            rightLabelText = rightButtonText + " " + task.targetStimulusType["name"];
        }
        updateSingleLabelText(leftButtonElement, leftButtonText, forAttribute, isMobile ? "center":"left");
        updateSingleLabelText(rightButtonElement, rightButtonText, forAttribute, isMobile ? "center":"right");
    }
    let leftResponseAction, rightResponseAction, correctionResponseAction;
    if (isMobile) {
        leftResponseAction = "<span style='color: red'>tap the left button.</span>";
        rightResponseAction = "<span style='color: red'>tap the right button.</span>";
        correctionResponseAction = "tap the other button.";
    } else {
        leftResponseAction = "<span style='color: red'>press the key " + task.leftKey["name"] + ".</span>";
        rightResponseAction = "<span style='color: red'>press the key " + task.rightKey["name"] + ".</span>";
        correctionResponseAction = "press the other key.";
    }
    let words = ["If", leftLabelText, "are presented,", leftResponseAction, "If",
        rightLabelText, "are presented,", rightResponseAction, "<br /> <br />",
        "<span style='color: red;' >Go Fast</span>. Some mistakes are <span style='color: red;'>OKAY</span>."];
    if (task.requiresCorrection) {
        words.push(" When an error message (the red <span style='color: red;'>X</span>) shows, " + correctionResponseAction);
    }
    if (isMobile) {
        words.push("<br /><br />Tap either button to continue.");
    } else {
        words.push("<br /><br />Press " + task.advanceKey["name"] + " to continue.");
        words.unshift( "<br /> <br /><br /> <br /><br /> <br />")
    }
    currentBlock.instruction = words.join(" ");
}

function updateSingleLabelText(label, text, forAttribute, alignment) {
    label.innerHTML = "<span style='color: " + (forAttribute ? task.attributeLabelColor:task.targetLabelColor) +
        "'>" + text + "</span>";
    label.style.textAlign = alignment;
    label.style.fontSize = properFontSize();
    if (label === leftButtonElement && !isMobile) {
        label.style.left = "2.5%";
    } else if (label === rightButtonElement && !isMobile) {
        label.style.right = "2.5%";
    }
}

function updateCombinedLabelText(label, attributeLabelText, targetLabelText) {
    label.innerHTML = "<span style='color: " + task.targetLabelColor +"'>" + targetLabelText +
        "</span><br />or<br /><span style='color: " + task.attributeLabelColor + "'>" + attributeLabelText + "</span>";
    label.style.textAlign = "center";
    if (label === leftButtonElement && !isMobile) {
        label.style.left = "0%";
    } else if (label === rightButtonElement && !isMobile) {
        label.style.right = "0%";
    }
    label.style.fontSize = properFontSize();
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function showEndingMessage() {
    if (task.endingMessage && task.endingMessage !== "null") {
        instructionElement.innerHTML = task.endingMessage;
        hideTaskElements();
        updateElementsVisibility([
            [instructionElement, "block"]
        ]);
        if (!isMobile) {
            window.removeEventListener("keydown", enterResponse);
        } else {
            updateElementsVisibility([
                [stimulusContainer, "none"]
            ]);
        }
        setTimeout(function () {
            jQuery("#NextButton").click();
        }, 1500);
    } else {
        jQuery("#NextButton").click();
    }
}

function showWarningMessage(errorMessage, timeout = true) {
    warningElement = document.getElementById("iat_custom_error");
    if (!warningElement) {
        warningElement = document.createElement("div");
        warningElement.setAttribute("style",
            "background-color: lightgray; color: red;");
        warningElement.fontSize = properFontSize();
        warningElement.id = "iat_custom_error";
        warningElement.appendChild(document.createTextNode(errorMessage));
        document.getElementById('Header').appendChild(warningElement);
    }
    updateElementsVisibility([[warningElement, "block"]]);
    warningElement.childNodes[0].nodeValue = errorMessage;
    if (timeout) {
        setTimeout(dismissErrorMessage, 1500);
    }
}

function dismissErrorMessage() {
    updateElementsVisibility([
        [warningElement, "none"],
        [errorElement, "none"],
    ]);
}

Qualtrics.SurveyEngine.addOnUnload(function()
{
    if (!isMobile) {
        window.removeEventListener("keydown", enterResponse);
    }
});
