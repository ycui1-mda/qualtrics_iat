# Qualtrics IAT Tool
A web app for generating the Implicit Association Test (IAT) running on Qualtrics

## Online Web App
The app is hosted by [Streamlit](https://streamlit.io/), a Python-based web framework. You can use the app here: 
[Qualtrics IAT Tool](https://share.streamlit.io/ycui1-mda/qualtrics_iat/qualtrics_iat/web_app.py).

## Run Web App Offline
Alternatively, you can run the app offline. The general steps are:
1. Download the latest version of the repository.
2. Install Python and Streamlit.
3. Run the web app in a Terminal with the command: `streamlit run your_directory/qualtrics_iat/web_app.py`

## Citation:
Cui Y., Robinson, J.D., Kim, S.K., Kypriotakis G., Green C.E., Shete S.S., & Cinciripini P.M., An open source web
app for creating and scoring Qualtrics-based implicit association test. arXiv:2111.02267 [q-bio.QM]

## Key Functionalities
The web app has three key functionalities: IAT Generator, Qualtrics Tools, and IAT Data Scorer. Each functionality
is clearly described on the web app regarding what parameters are expected and what they mean. If you have any
questions, please feel free to leave a comment or send your inquiries to me.

### IAT Generator
In this section, you can generate the Qualtrics survey template to run the IAT experiment. Typically, you
need to consider specifying the following parameters. We'll use the classic flower-insect IAT as an example. As
a side note, there are a few other IAT tasks (e.g., gender-career) in the app for your reference.

- *Positive Target Concept*: Flower
- *Negative Target Concept*: Insect
- *Positive Target Stimuli*: Orchid, Tulip, Rose, Daffodil, Daisy, Lilac, Lily
- *Negative Target Stimuli*: Wasp, Flea, Roach, Centipede, Moth, Bedbug, Gnat
- *Positive Attribute Concept*: Pleasant
- *Negative Attribute Concept*: Unpleasant
- *Positive Attribute Stimuli*: Joy, Happy, Laughter, Love, Friend, Pleasure, Peace, Wonderful
- *Negative Attribute Stimuli*: Evil, Agony, Awful, Nasty, Terrible, Horrible, Failure, War

Once you specify these parameters, you can generate a Qualtrics template file, from which you can create a Qualtrics
survey that is ready to be administered. Please note that not all Qualtrics account types support creating surveys
from a template. Alternatively, you can obtain the JavaScript code of running the IAT experiment and add the code
to a Qualtrics question. If you do this, please make sure that you set the proper embedded data fields.

## Qualtrics Tools
In this section, you can directly interact with the Qualtrics server by invoking its APIs. To use these APIs, you
need to obtain the token in your account settings. Key functionalities include:

- **Upload Images to Qualtrics Graphic Library**:
You can upload images from your local computer to your Qualtrics Graphics Library. You need to specify the library
ID # and the name of the folder to which the images will be uploaded. If the upload succeeds, the web app will return
the URLs for these images. You can set these URLs as stimuli in the IAT if your experiment uses pictures.

- **Create Surveys**:
You can create surveys by uploading a QSF file or the JSON text. Please note that the QSF file uses JSON as its 
content. If you're not sure about the JSON content, you can inspect a template file.

- **Export Survey Responses**:
You can export a survey's responses for offline processing. You need to specify the library ID # and the export file
format (e.g., csv).

- **Delete Images**:
You can delete images from your Qualtrics Graphics Library. You need to specify the library ID # and the IDs for 
the images that you want to delete.

- **Delete Survey**:
You can delete surveys from your Qualtrics Library. You need to specify the survey ID #.

## IAT Data Scorer
In this section, you can score the IAT data from the exported survey response. Currently, there are two calculation
algorithms supported: the conventional and the improved.

Citation for the algorithms: Greenwald et al. Understanding and Using the Implicit Association Test: I. An 
Improved Scoring Algorithm. Journal of Personality and Social Psychology 2003 (85)2:192-216

### The Conventional Algorithm
1. Use data from B4 & B7 (counter-balanced order will be taken care of in the calculation).
2. Nonsystematic elimination of subjects for excessively slow responding and/or high error rates.
3. Drop the first two trials of each block.
4. Recode latencies outside 300/3,000 boundaries to the nearer boundary value. 
5. 5.Log-transform the resulting values.
6. Average the resulting values for each of the two blocks.
7. Compute the difference: B7 - B4.

### The Improved Algorithm
1. Use data from B3, B4, B6, & B7 (counter-balanced order will be taken care of in the calculation).
2. Eliminate trials with latencies > 10,000 ms; Eliminate subjects for whom more than 10% of trials have latency 
less than 300 ms. 
3. Use all trials; Delete trials with latencies below 400 ms (alternative).
4. Compute mean of correct latencies for each block. Compute SD of correct latencies for each block (alternative).
5. Compute one pooled SD for all trials in B3 & B6, another for B4 & B7; Compute one pooled SD for correct trials 
in B3 & B6, another for B4 & B7 (alternative).
6. Replace each error latency with block mean (computed in Step 5) + 600 ms; Replace each error latency with 
block mean + 2 x block SD of correct responses (alternative 1); Use latencies to correct responses when correction to 
error responses is required (alternative 2).
7. Average the resulting values for each of the four blocks.
8. Compute two differences: B6 - B3 and B7 - B4.
9. Divide each difference by its associated pooled-trials SD.
10. Average the two quotients.

## Questions?
If you have any questions or would like to contribute to this project, please send me an email: ycui1@mdanderson.org.

## License
MIT License