""""""

from enum import Enum
import pandas as pd
import numpy as np


class IATData:
    """Data model to handle the IAT data generated from the Qualtrics IAT survey"""
    mock_study = "iat"
    
    def __init__(self,
                 data_file,
                 grouped_by=("study", "ResponseId"),
                 trial_response_separator="_",
                 suffix_responses="Responses",
                 suffix_trials="Trials",
                 suffix_conditions="blockConditions",
                 congruency_labels=None):
        """Initialize the data model instance of the IATData
        :param data_file: Union[csv, zip, Bytes], the data file containing the IAT survey responses
        :param grouped_by: tuple, the indices that identify distinct IAT sessions
        :param trial_response_separator: str, the separator between responses in the embedded data
        :param suffix_responses: str, the suffix of the embedded field for saving trial responses
        :param suffix_trials: str, the suffix of the embedded field for saving trial stimuli
        :param suffix_conditions: str, the suffix of the embedded field for saving the block conditions
        :param congruency_labels: Union[None, dict], the labels by congruency
        :return None
        """
        self.suffix_responses, self.suffix_trials, self.suffix_conditions = \
            suffices = suffix_responses, suffix_trials, suffix_conditions
        self.grouped_by = grouped_by
        if not congruency_labels:
            congruency_labels = {"con": ("p+", "n-"), "inc": ("p-", "n+")}
        self.congruency_labels = congruency_labels
        self.trial_response_separator = trial_response_separator
        self.iat_data_clean = None
        
        _iat_data = pd.read_csv(data_file)
        self.iat_data = _iat_data[_iat_data[grouped_by[1]].str.startswith('R_')].reset_index(drop=True)
        
        responses_field_name = f"block1{suffix_responses}"
        self.studies = {x.split("_")[0] for x in self.iat_data.columns
                        if len(x) > len(responses_field_name) and x.endswith(responses_field_name)}
        # Create a mock study to streamline the data processing process as if there are multiple studies
        if not self.studies:
            self.studies = {self.mock_study}
            old_block_names = [x for x in self.iat_data.columns if x.endswith(suffices)]
            new_block_names = [f"{self.mock_study}_{x}" for x in old_block_names]
            self.iat_data.rename(columns=dict(zip(old_block_names, new_block_names)), inplace=True)
            
    def __repr__(self):
        return f"{self.__class__.__name__}('data_file', grouped_by={self.grouped_by}, " \
               f"trial_response_separator={self.trial_response_separator!r}, " \
               f"suffix_responses={self.suffix_responses!r}, " \
               f"suffix_trials={self.suffix_trials!r}, " \
               f"suffix_conditions={self.suffix_conditions!r}, " \
               f"congruency_labels={self.congruency_labels})"
        
    def _transpose_block_wide_to_long(self, suffix, separator, trial_data_name):
        """Transpose block data from the wide format to the long format, trial responses and stimuli
        :param suffix: str, determine the columns to be processed
        :param separator: str, the separator between consecutive trials
        :param trial_data_name: str, the trial data column name
        :return DataFrame, the transposed DataFrame
        :raise ValueError when found no columns for the responses data"""
        block_cols = [x for x in self.iat_data.columns if x.endswith(suffix)]
        if not block_cols:
            if suffix == self.suffix_trials:
                # it can happen when the researchers don't record the trial stimuli data
                return pd.DataFrame(
                    columns=[*reversed(self.grouped_by), "block_number", "trial_number", trial_data_name])
            else:
                raise ValueError("No columns were found for the responses data")
            
        block_wide = self.iat_data.melt(
            id_vars=self.grouped_by[1],
            value_vars=block_cols,
            value_name="block_data",
            var_name="block_counter"
        ).dropna()
        block_wide[self.grouped_by[0]] = block_wide["block_counter"].str[:-len(f"block1{suffix}") - 1]
        block_wide["block_number"] = block_wide["block_counter"].str[-len(suffix) - 1].map(int)
        trial_data = block_wide['block_data'].str.split(separator, expand=True)
        trial_columns = [x + 1 for x in trial_data.columns]
        block_wide[trial_columns] = trial_data
        block_long = block_wide.melt(
            id_vars=[*reversed(self.grouped_by), "block_number"],
            value_vars=trial_columns,
            value_name=trial_data_name,
            var_name="trial_number"
        ).dropna()
        return block_long
    
    def _transpose_block_conditions(self, study):
        """Create the block conditions by study"""
        condition_data = self.iat_data[[self.grouped_by[1], f"{study}_{self.suffix_conditions}"]].copy()
        study_conditions = condition_data[f"{study}_{self.suffix_conditions}"].str.split("|", expand=True)
        block_counters = [x + 1 for x in study_conditions.columns]
        condition_data[block_counters] = study_conditions
        condition_data[self.grouped_by[0]] = study
        return condition_data.melt(
            id_vars=reversed(self.grouped_by),
            value_vars=block_counters,
            value_name="block_condition",
            var_name="block_number"
        )
    
    def clean_up(self):
        """Clean up the IAT data response
        :return The cleaned up trial-level DataFrame
        :raise
            ValueError, when the response can't be casted
            AssertionError, when the trial number isn't the same from the trial number generated from its positioning
        """
        
        latency_data = self._transpose_block_wide_to_long(
            self.suffix_responses, self.trial_response_separator, "trial_response")
        stimulus_data = self._transpose_block_wide_to_long(
            self.suffix_trials, ",", "trial_stimulus")
        if not stimulus_data.empty:
            trial_data = latency_data.merge(stimulus_data,
                                            on=[*reversed(self.grouped_by), "block_number", "trial_number"])
        else:
            trial_data = latency_data
        
        def _score_trial_response(x):
            scored_data = [np.nan, np.nan, np.nan]
            if isinstance(x, str) and x != "None":
                try:
                    correct_index = max(x.find("Y"), x.find("N"))
                    if correct_index > 0:
                        scored_data = int(x[:correct_index]), x[correct_index], int(x[correct_index + 1:])
                except ValueError:
                    raise ValueError("can't cast the response")
            return pd.Series(scored_data)
        
        trial_cols = 'trial_counter trial_correct reaction_time'.split()
        trial_data[trial_cols] = trial_data['trial_response'].apply(_score_trial_response)
        trial_number_error_msg = "Split trial numbers are different from the trial number prefixes in the " \
                                 "block responses."
        assert pd.Series((trial_data["trial_number"] != trial_data["trial_counter"])).sum() == 0, trial_number_error_msg

        conditions = {label: x for x, labels in self.congruency_labels.items() for label in labels}
        block_conditions = pd.concat([self._transpose_block_conditions(study) for study in self.studies])
        block_conditions["task"] = block_conditions["block_condition"].map(
            lambda x: conditions.get(x, "sin")
        )
        block_conditions['task_block_counter'] = block_conditions.groupby([*reversed(self.grouped_by), "task"]).\
            cumcount().map(lambda x: x+1)
        
        trial_merged = trial_data.merge(block_conditions, on=[*reversed(self.grouped_by), "block_number"])
        
        self.iat_data_clean = trial_merged.drop(["trial_counter", "trial_response"], axis=1).sort_values(
            by=[*self.grouped_by, "block_number"]).dropna().reset_index(drop=True)
        return self.iat_data_clean


class IATAlgorithmName(Enum):
    """The list of supported algorithms"""
    CONVENTIONAL = "conventional"
    IMPROVED = "improved"
    

class IATErrorPenalty(Enum):
    """Error latency penalty approach"""
    ABSOLUTE = 0
    RELATIVE = 1
    BLOCK_MEAN = 2
    
    @property
    def description(self):
        """Description of the error penalty approach"""
        if self == self.ABSOLUTE:
            return "Block mean of correct responses + penalty time in ms"
        elif self == self.RELATIVE:
            return "Block mean of correct responses + penalty time in SD unit"
        else:
            return "Use latency to correct responses when correction is required after an error"


class IATAlgorithm:
    """Data model for the algorithm used in IAT data scoring"""
    def __init__(self, name, **params):
        """Initialize the instance for the algorithm
        :param name: str, the name of the algorithm
        :param params: dict, additional parameters for the algorithm
            When the algorithm is conventional, the following keyword parameters are supported:
                included_blocks: list, the blocks to be used for scoring
                rt_low_cutoff: int, float, the reaction time low cutoff
                rt_high_cutoff: int, float, the reaction time high cutoff
                recode_outliers: bool, whether outliers are recoded
                trials_to_drop: int, the number of trials at a block's beginning to drop
                allowed_error_rate: float, the percentage of error rate to drop subjects
                allowed_rt_upper: float, the minimum mean reaction time allowed to be included in the scoring
                
            When the algorithm is improved, the following keyword parameters are supported:
                included_blocks: list, the blocks to be used for scoring
                rt_low_cutoff: int, float, the reaction time low cutoff
                rt_high_cutoff: int, float, the reaction time high cutoff
                allowed_fast_rate: float, the percentage of fast responses, above which subjects are eliminated
                use_all_trials: bool, whether all trials are used after removing slow and fast responses
                rt_delete_cutoff: float, below which the trials are deleted, it's only valid when use_all_trials False
                pooled_sd_using_all: bool, whether to use all trials or only the correct trials to calculate SD
                replacement_option: IATErrorPenalty or 0, 1, 2, how to replace error trials
                rt_punishment: int or float, the penalty adjustment for error trials
            """
        self.name = name
        self.iat_data = None
        if name == IATAlgorithmName.CONVENTIONAL.name.lower():
            self.included_blocks = params.get("included_blocks", [4, 7])
            self.rt_low_cutoff = params.get("rt_low_cutoff", 300)
            self.rt_high_cutoff = params.get("rt_high_cutoff", 3000)
            self.recode_outliers = params.get("recode_outliers", True)
            self.trials_to_drop = params.get("trials_to_drop", 2)
            self.allowed_error_rate = params.get("allowed_error_rate", 0.1)
            self.allowed_rt_upper = params.get("allowed_rt_upper", 3000)
        elif name == IATAlgorithmName.IMPROVED.name.lower():
            self.included_blocks = params.get("included_blocks", [3, 4, 6, 7])
            self.rt_low_cutoff = params.get("rt_low_cutoff", 300)
            self.rt_high_cutoff = params.get("rt_high_cutoff", 10000)
            self.allowed_fast_rate = params.get("allowed_fast_rate", 0.1)
            self.use_all_trials = params.get("use_all_trials", True)
            self.rt_delete_cutoff = params.get("rt_delete_cutoff", 400)
            self.pooled_sd_using_all = params.get("pooled_sd_using_all", True)
            self.replacement_option = params.get("replacement_option", IATErrorPenalty.ABSOLUTE.value)
            self.rt_punishment = params.get("rt_punishment", 600)
            
    def __repr__(self):
        """Define the string representation of the instance"""
        params = self.__dict__.copy()
        del params["name"], params["iat_data"]
        params_str = ", ".join("=".join(map(str, item)) for item in params.items())
        return f"{self.__class__.__name__}({self.name!r}, {params_str})"
    
    def __str__(self):
        """Define the string when the instance is printed"""
        if self.name == IATAlgorithmName.CONVENTIONAL.name.lower():
            return f"""\nIncluded Blocks: {str(self.included_blocks)[1:-1]}\n
Reaction Time (Low Cutoff): {self.rt_low_cutoff} ms\n
Reaction Time (High Cutoff): {self.rt_high_cutoff} ms\n
Recode Outliers: {"Yes" if self.recode_outliers else "No"}\n
The First X Trials to Drop: {self.trials_to_drop}\n
Allowed Error Rate: {self.allowed_error_rate:.2%}\n
Allowed Latency Limit as Slow Responders: mean RT >{self.allowed_rt_upper} ms\n"""
        else:
            return f"""\nIncluded Blocks: {str(self.included_blocks)[1:-1]}\n
Reaction Time (Low Cutoff): {self.rt_low_cutoff} ms\n
Reaction Time (High Cutoff): {self.rt_high_cutoff} ms\n
Allowed Fast Rate: {self.allowed_fast_rate:.2%}\n
Use All Trials (if no, use the rt cutoff below to remove trials): {"Yes" if self.use_all_trials else "No"}\n
Reaction Time Cutoff (for deletion) = {self.rt_delete_cutoff}ms\n
Pooled SD: {"Using all trials" if self.pooled_sd_using_all else "Using correct trials only"}\n
Error Trial Replacement: {IATErrorPenalty(self.replacement_option).description}\n
Error Trial Penalty (ms or SD unit): {self.rt_punishment}"""
    
    def _calculate_reliability(self, trial_data, scored_iat_df=None):
        """Calculate the reliability of the IAT measure
        :param trial_data: DataFrame, the trial level data
        :param scored_iat_df: DataFrame, the scored IAT DataFrame, only applies for the improved algorithm
        """
        reliability_scores = list()
        
        def _compute_reliability_score(merged_df, col1, col2):
            def _spearman_brown_formula(x):
                return 2 * x / (1 + x)
    
            iat_corr = merged_df.groupby(self.iat_data.grouped_by[0])[[col1, col2]].corr().iloc[0::2, -1]
            iat_corr.index = iat_corr.index.droplevel(1)
            return iat_corr.map(_spearman_brown_formula)
        
        if self.name == IATAlgorithmName.CONVENTIONAL.name.lower():
            used_column = "iat_score_logged"
            _algorithm = self._process_data_conventional
        else:
            used_column = "iat_score"
            _algorithm = self._process_data_improved
            reliability_scores.append(_compute_reliability_score(scored_iat_df, "iat_score_1", "iat_score_2"))
        
        used_columns = [*self.iat_data.grouped_by, used_column]
        _, odd_scored_iat_df = _algorithm(trial_data[trial_data["trial_number"] % 2 == 1])
        _, even_scored_iat_df = _algorithm(trial_data[trial_data["trial_number"] % 2 == 0])
        odd_even_iat = odd_scored_iat_df[used_columns].merge(
            even_scored_iat_df[used_columns],
            on=self.iat_data.grouped_by,
            suffixes=("_odd", "_even")
        )
        reliability_scores.append(_compute_reliability_score(odd_even_iat, f"{used_column}_odd", f"{used_column}_even"))
        
        return reliability_scores
    
    def _apply_conventional(self):
        """Apply the conventional algorithm
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        trial_data = self.iat_data.iat_data_clean
        summary_df, scored_iat_df = self._process_data_conventional(trial_data)
        summary_df["reliability_by_odd_even"] = self._calculate_reliability(trial_data)
        return self._clean_up_scored_data(summary_df, scored_iat_df)
    
    def _process_data_shared(self, trial_data):
        iat_data_report = pd.DataFrame()
        grouped_by = list(self.iat_data.grouped_by)
    
        # The total trial count by session
        iat_data_report["total_trial_count"] = trial_data.groupby(grouped_by).size()
        iat_data_report["total_error_trial_count"] = \
            trial_data[trial_data["trial_correct"] == "N"].groupby(grouped_by).size()
        iat_data_report["overall_error_rate"] = \
            iat_data_report["total_error_trial_count"] / iat_data_report["total_trial_count"]
        iat_data_report.fillna(0, inplace=True)
        return iat_data_report, grouped_by
    
    def _process_data_conventional(self, trial_data: pd.DataFrame):
        """Process data using the conventional algorithm
        :param trial_data: DataFrame, the trial-level data to be scored
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        iat_data_report, grouped_by = self._process_data_shared(trial_data)
        
        # Use the needed blocks and trials
        used_data = trial_data[trial_data['block_number'].isin(self.included_blocks) &
                               (trial_data['trial_number'] > self.trials_to_drop)].reset_index(drop=True)

        # The used trial count by session
        iat_data_report["used_trial_count"] = used_data.groupby(grouped_by).size()
        
        # Identify the error rates
        iat_data_report["error_trial_count"] = used_data[used_data['trial_correct'] == "N"].groupby(grouped_by).size()
        iat_data_report["error_trial_count"].fillna(0, inplace=True)
        iat_data_report["error_rate"] = iat_data_report["error_trial_count"] / iat_data_report["used_trial_count"]
        
        # Identify the average response time using all included trials
        iat_data_report["rt_mean"] = used_data.groupby(grouped_by)["reaction_time"].mean()
        
        included_responses = iat_data_report[
            (iat_data_report['error_rate'] < self.allowed_error_rate) &
            (iat_data_report['rt_mean'] < self.allowed_rt_upper)
            ].reset_index()[grouped_by]
        
        used_data = included_responses.merge(used_data, how="left", on=grouped_by)
        
        if self.recode_outliers:
            used_data['rt_recoded'] = used_data['reaction_time'].clip(
                lower=self.rt_low_cutoff,
                upper=self.rt_high_cutoff
            )
        else:
            used_data['rt_recoded'] = used_data['reaction_time'].map(
                lambda x: x if self.rt_low_cutoff <= x <= self.rt_high_cutoff else np.nan
            )
        used_data['rt_logged'] = np.log10(used_data['rt_recoded'])
        
        rt_mean_df = used_data.groupby([*grouped_by, 'task'], as_index=False).mean()
        calculated_iat = rt_mean_df.pivot(
            index=grouped_by,
            columns='task',
            values=['rt_recoded', 'rt_logged']
        ).reset_index()
        calculated_iat.columns = [x[0] + '_' + x[1] if x[1] else x[0] for x in calculated_iat.columns]
        
        calculated_iat['iat_score_raw'] = calculated_iat['rt_recoded_inc'] - calculated_iat['rt_recoded_con']
        calculated_iat['iat_score_logged'] = calculated_iat['rt_logged_inc'] - calculated_iat['rt_logged_con']
        
        scored_iat_df = iat_data_report.reset_index().merge(calculated_iat, how="left", on=grouped_by)
        summary_gb = scored_iat_df.groupby("study")
        summary_df = summary_gb.agg(
            trial_count_all_blocks=("total_trial_count", sum),
            trial_count_used_blocks=("used_trial_count", sum),
            trial_count_error=("error_trial_count", sum),
            pct_error_min_total=("overall_error_rate", np.min),
            pct_error_max_total=("overall_error_rate", np.max),
            pct_error_sd_total=("overall_error_rate", np.std),
            pct_error_mean_total=("overall_error_rate", np.mean),
            pct_error_mean_used_trials=("error_rate", np.mean),
            iat_raw_score_mean=("iat_score_raw", np.mean),
            iat_raw_score_min=("iat_score_raw", np.min),
            iat_raw_score_max=("iat_score_raw", np.max),
            iat_raw_score_sd=("iat_score_raw", np.std),
            rt_raw_con_mean=("rt_recoded_con", np.mean),
            rt_raw_con_min=("rt_recoded_con", np.min),
            rt_raw_con_max=("rt_recoded_con", np.max),
            rt_raw_con_sd=("rt_recoded_con", np.std),
            rt_raw_inc_mean=("rt_recoded_inc", np.mean),
            rt_raw_inc_min=("rt_recoded_inc", np.min),
            rt_raw_inc_max=("rt_recoded_inc", np.max),
            rt_raw_inc_sd=("rt_recoded_inc", np.std),
            iat_log_score_mean=("iat_score_logged", np.mean),
            iat_log_score_min=("iat_score_logged", np.min),
            iat_log_score_max=("iat_score_logged", np.max),
            iat_log_score_sd=("iat_score_logged", np.std),
            rt_log_con_mean=("rt_logged_con", np.mean),
            rt_log_con_min=("rt_logged_con", np.min),
            rt_log_con_max=("rt_logged_con", np.max),
            rt_log_con_sd=("rt_logged_con", np.std),
            rt_log_inc_mean=("rt_logged_inc", np.mean),
            rt_log_inc_min=("rt_logged_inc", np.min),
            rt_log_inc_max=("rt_logged_inc", np.max),
            rt_log_inc_sd=("rt_logged_inc", np.std)
        )
        return summary_df, scored_iat_df
    
    def _process_data_improved(self, trial_data: pd.DataFrame):
        """Process data using the improved algorithm
        :param trial_data: DataFrame, the trial-level data to be scored
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        iat_data_report, grouped_by = self._process_data_shared(trial_data)
        
        # Use the needed blocks
        used_data = trial_data[trial_data['block_number'].isin(self.included_blocks)].reset_index(drop=True)
    
        # The used trial count by session
        iat_data_report["used_trial_count"] = used_data.groupby(grouped_by).size()
    
        # Identify the high latency trials
        used_data["above_rt_upper_limit"] = used_data['reaction_time'] > self.rt_high_cutoff
        iat_data_report["high_latency_trial_count"] = \
            used_data[used_data["above_rt_upper_limit"]].groupby(grouped_by).size()
    
        # Identify the sessions with high fast trials
        iat_data_report["fast_trial_count"] = \
            used_data[used_data['reaction_time'] < self.rt_low_cutoff].groupby(grouped_by).size()
        iat_data_report["fast_trial_pct"] = iat_data_report["fast_trial_count"] / iat_data_report["used_trial_count"]
        too_many_fast_trial = pd.DataFrame((iat_data_report["fast_trial_pct"] > self.allowed_fast_rate).
                                           rename("too_many_fast_trial")).reset_index()
        used_data_merged = used_data.merge(too_many_fast_trial, on=grouped_by)
    
        # Identify the trials with fast responses that can be deleted if the option is selected
        used_data_merged["below_rt_fast_limit"] = used_data_merged['reaction_time'] < self.rt_delete_cutoff
        iat_data_report["fast_latency_trial_count"] = \
            used_data_merged[used_data_merged["below_rt_fast_limit"]].groupby(grouped_by).size()
    
        # Eliminate the trials with high latency and the sessions with high percentage of fast trials
        keep_condition = ~used_data_merged["above_rt_upper_limit"] & ~used_data_merged["too_many_fast_trial"]
    
        # Delete the fast trials if applicable
        if not self.use_all_trials:
            keep_condition = keep_condition & ~used_data_merged["below_rt_fast_limit"]
    
        used_data = used_data_merged[keep_condition].copy()
    
        iat_data_report["final_used_trial_count"] = used_data.groupby(grouped_by).size()
        iat_data_report["error_trial_count"] = used_data[used_data["trial_correct"] == "N"].groupby(grouped_by).size()
        iat_data_report["error_rate"] = iat_data_report["error_trial_count"] / iat_data_report["final_used_trial_count"]
        iat_data_report.fillna(0, inplace=True)
    
        def _make_na_values(x):
            if x["final_used_trial_count"] == 0:
                x["error_trial_count"] = x["error_rate"] = np.nan
            return pd.Series([x["error_trial_count"], x["error_rate"]])
    
        iat_data_report[["error_trial_count", "error_rate"]] = iat_data_report.apply(_make_na_values, axis=1)
    
        # Recode error latencies
        error_penalty = IATErrorPenalty(self.replacement_option)
        if error_penalty in (IATErrorPenalty.ABSOLUTE, IATErrorPenalty.RELATIVE):
            rt_block = used_data[used_data['trial_correct'] == "Y"]. \
                groupby([*grouped_by, 'block_number'])['reaction_time']. \
                mean().rename('rt_block_mean').reset_index()
            used_data = used_data.merge(rt_block, on=[*grouped_by, 'block_number'])
            if error_penalty == IATErrorPenalty.RELATIVE:
                std_block = used_data[used_data['trial_correct'] == "Y"]. \
                    groupby([*grouped_by, 'block_number'])['reaction_time']. \
                    std().rename('rt_block_std').reset_index()
                used_data = used_data.merge(std_block, on=[*grouped_by, 'block_number'])
        
            def _recode_error_latency(x):
                if x['trial_correct'] == 'Y':
                    return x['reaction_time']
                if error_penalty == IATErrorPenalty.ABSOLUTE:
                    return x['rt_block_mean'] + self.rt_punishment
                return x['rt_block_mean'] + self.rt_punishment * x['rt_block_std']
        
            used_data['rt_recoded'] = used_data.apply(_recode_error_latency, axis=1)
        else:
            used_data['rt_recoded'] = used_data['reaction_time']
    
        rt_task = used_data.groupby([*grouped_by, 'task', 'task_block_counter'], as_index=False)['rt_recoded'].mean()
        iat_scores_task = rt_task.pivot(
            index=[*grouped_by, 'task_block_counter'],
            values=['rt_recoded'],
            columns=['task']
        ).reset_index()
        iat_scores_task.columns = [x[0] + '_' + x[1] if x[1] else x[0] for x in iat_scores_task.columns]
    
        pooled_std = (used_data if self.pooled_sd_using_all else used_data[used_data['trial_correct'] == "Y"]). \
            groupby([*grouped_by, 'task_block_counter'])['reaction_time'].std().rename('pooled_std').reset_index()
        iat_scores = iat_scores_task.merge(pooled_std, on=[*grouped_by, 'task_block_counter'])
        iat_scores['iat_score'] = \
            (iat_scores['rt_recoded_inc'] - iat_scores['rt_recoded_con']) / iat_scores['pooled_std']
    
        iat_scores_session = iat_scores.pivot(
            index=grouped_by,
            values=["rt_recoded_con", "rt_recoded_inc", "pooled_std", "iat_score"],
            columns='task_block_counter'
        ).reset_index()
    
        iat_scores_session.columns = [f"{x[0]}_{x[1]}" if x[1] else x[0] for x in iat_scores_session.columns]
    
        def _calculate_means(x):
            iat_score_mean = np.mean(x[["iat_score_1", "iat_score_2"]])
            rt_recoded_con_mean = np.mean(x[["rt_recoded_con_1", "rt_recoded_con_2"]])
            rt_recoded_inc_mean = np.mean(x[["rt_recoded_inc_1", "rt_recoded_inc_2"]])
            return pd.Series([iat_score_mean, rt_recoded_con_mean, rt_recoded_inc_mean])
    
        iat_scores_session["iat_score rt_recoded_con rt_recoded_inc".split()] = \
            iat_scores_session.apply(_calculate_means, axis=1)
    
        scored_iat_df = iat_data_report.reset_index().merge(iat_scores_session, on=grouped_by, how="left")
    
        summary_gb = scored_iat_df.groupby("study")
        summary_df = summary_gb.agg(
            total_response_count=("final_used_trial_count", lambda x: (x > -1).sum()),
            used_response_count=("final_used_trial_count", lambda x: (x > 0).sum()),
            excluded_response_count=("final_used_trial_count", lambda x: (x < 1).sum()),
            trial_count_all_blocks=("total_trial_count", sum),
            trial_count_errors_all_blocks=("total_error_trial_count", sum),
            pct_error_min_total=("overall_error_rate", np.min),
            pct_error_max_total=("overall_error_rate", np.max),
            pct_error_sd_total=("overall_error_rate", np.std),
            pct_error_mean_total=("overall_error_rate", np.mean),
            trial_count_used_blocks=("used_trial_count", sum),
            trial_count_high_latency=("high_latency_trial_count", sum),
            trial_count_fast=("fast_trial_count", sum),
            pct_fast_mean=("fast_trial_pct", np.mean),
            trial_count_fast_latency=("fast_latency_trial_count", sum),
            trial_count_final=("final_used_trial_count", sum),
            trial_count_errors_used_trials=("error_trial_count", sum),
            pct_error_mean_used_trials=("error_rate", np.mean),
            iat_score_mean=("iat_score", np.mean),
            iat_score_min=("iat_score", np.min),
            iat_score_max=("iat_score", np.max),
            iat_score_sd=("iat_score", np.std),
            rt_con_mean=("rt_recoded_con", np.mean),
            rt_con_min=("rt_recoded_con", np.min),
            rt_con_max=("rt_recoded_con", np.max),
            rt_con_sd=("rt_recoded_con", np.std),
            rt_inc_mean=("rt_recoded_inc", np.mean),
            rt_inc_min=("rt_recoded_inc", np.min),
            rt_inc_max=("rt_recoded_inc", np.max),
            rt_inc_sd=("rt_recoded_inc", np.std),
        )
        return summary_df, scored_iat_df
    
    def _apply_improved(self):
        """Apply the improved algorithm
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        trial_data = self.iat_data.iat_data_clean
        summary_df, scored_iat_df = self._process_data_improved(trial_data)
        summary_df["reliability_by_task"], summary_df["reliability_by_odd_even"] = \
            tuple(self._calculate_reliability(trial_data, scored_iat_df))
        return self._clean_up_scored_data(summary_df, scored_iat_df)
    
    def _clean_up_scored_data(self, summary_df, scored_iat_df):
        """Clean up the return data set
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        overall_summary_df = summary_df.reset_index()
        if len(self.iat_data.studies) == 1 and self.iat_data.studies.pop() == IATData.mock_study:
            scored_iat_df.drop(columns=self.iat_data.grouped_by[0], inplace=True)
            overall_summary_df.drop(columns=self.iat_data.grouped_by[0], inplace=True)
        return overall_summary_df, scored_iat_df
    
    def process_data(self, iat_data: IATData):
        """Process the data using the current algorithm
        :param iat_data: IATData, the IATData instance
        :return tuple, (DataFrame, DataFrame), the scored summary and response-level data"""
        self.iat_data = iat_data
        if self.name == IATAlgorithmName.CONVENTIONAL.value:
            return self._apply_conventional()
        elif self.name == IATAlgorithmName.IMPROVED.value:
            return self._apply_improved()
