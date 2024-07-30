import * as React from 'react';
import { OrderedMap, OrderedSet, Map } from 'immutable';
import { Switch, Button, ButtonGroup, EmptyState, Autocomplete, Modal } from 'superdesk-ui-framework/react';
import { ToggleBoxNext } from 'superdesk-ui-framework';

import { IArticle, IArticleSideWidget, ISuperdesk } from 'superdesk-api';

import { getTagsListComponent } from './tag-list';
import { getNewItemComponent } from './new-item';
import { ITagUi } from './types';
import { toClientFormat, IServerResponse, toServerFormat } from './adapter';
import { getGroups } from './groups';
import { getAutoTaggingVocabularyLabels } from './common';
import { getExistingTags, createTagsPatch } from './data-transformations';
import { noop } from 'lodash';

export const entityGroups = OrderedSet(['place', 'person', 'organisation', 'event',]);

export type INewItem = Partial<ITagUi>;

interface IAutoTaggingResponse {
    analysis: OrderedMap<string, ITagUi>;
}

interface IAutoTaggingSearchResult {
    result: {
        tags: IServerResponse;

        /**
         * When search is performed, this will contain
         * all parents of items that matched the search query
         * and were returned in `tags` section.
         */
        broader?: IServerResponse;
    };
}

type IProps = React.ComponentProps<IArticleSideWidget['component']>;

interface ISemaphoreFields {
    [key: string]: {
        name: string;
        order: number;
    };
}

type IEditableData = { original: IAutoTaggingResponse; changes: IAutoTaggingResponse };

interface IState {
    runAutomaticallyPreference: boolean | 'loading';
    data: 'not-initialized' | 'loading' | IEditableData;
    newItem: INewItem | null;
    vocabularyLabels: Map<string, string> | null;
    tentativeTagName: string;
    forceRenderKey: number;
    log: string | 'error';
}

const RUN_AUTOMATICALLY_PREFERENCE = 'run_automatically';

function tagAlreadyExists(data: IEditableData, qcode: string): boolean {
    return data.changes.analysis.has(qcode);
}

export function hasConfig(key: string, semaphoreFields: ISemaphoreFields) {
    return semaphoreFields[key] != null;
}
// Runs when clicking the "Run" button. Returns the tags from the semaphore service
export function getAutoTaggingData(data: IEditableData, semaphoreConfig: any) {
    const items = data.changes.analysis;
    const isEntity = (tag: ITagUi) => tag.group && entityGroups.has(tag.group.value);

    const entities = items.filter((tag) => isEntity(tag));
    const entitiesGrouped = entities.groupBy((tag) => tag?.group.value);

    const entitiesGroupedAndSortedByConfig = entitiesGrouped
        .filter((_, key) => hasConfig(key, semaphoreConfig.entities))
        .sortBy((_, key) => semaphoreConfig.entities[key].order,
            (a, b) => a - b);
    const entitiesGroupedAndSortedNotInConfig = entitiesGrouped
        .filter((_, key) => !hasConfig(key, semaphoreConfig.entities))
        .sortBy((_, key) => key!.toString().toLocaleLowerCase(),
            (a, b) => a.localeCompare(b));
    const entitiesGroupedAndSorted = entitiesGroupedAndSortedByConfig
        .concat(entitiesGroupedAndSortedNotInConfig);

    const others = items.filter((tag) => isEntity(tag) === false);
    const othersGrouped = others.groupBy((tag) => tag.group.value);

    return { entitiesGroupedAndSorted, othersGrouped };
}

function showAutoTaggerServiceErrorModal(superdesk: ISuperdesk, errors: Array<ITagUi>) {
    const { gettext } = superdesk.localization;
    const { showModal } = superdesk.ui;

    showModal(({ closeModal }) => (
        <Modal
            headerTemplate={gettext('Autotagger service error')}
            footerTemplate={(
                <Button
                    aria-label="close"
                    text={gettext('close')}
                    onClick={() => {
                        closeModal();
                    }}
                />
            )}
        >
            <h3>{gettext('Some tags can not be displayed')}</h3>

            <p>
                {
                    gettext(
                        'Autotagger service has returned tags '
                        + 'referencing parents that do not exist in the response.',
                    )
                }
            </p>

            <table className="table">
                <thead>
                    <th>{gettext('tag name')}</th>
                    <th>{gettext('qcode')}</th>
                    <th>{gettext('parent ID')}</th>
                </thead>

                <tbody>
                    {
                        errors.map((tag) => (
                            <tr key={tag.qcode}>
                                <td>{tag.name}</td>
                                <td>{tag.qcode}</td>
                                <td>{tag.parent}</td>
                            </tr>
                        ))
                    }
                </tbody>
            </table>
        </Modal>
    ));
}

export function getAutoTaggingComponent(superdesk: ISuperdesk, label: string): IArticleSideWidget['component'] {
    const { preferences } = superdesk;
    const { httpRequestJsonLocal } = superdesk;
    const { gettext, gettextPlural } = superdesk.localization;
    const { memoize, generatePatch, arrayToTree } = superdesk.utilities;
    const { AuthoringWidgetHeading, Alert } = superdesk.components;
    const groupLabels = getGroups(superdesk);

    const TagListComponent = getTagsListComponent(superdesk);
    const NewItemComponent = getNewItemComponent(superdesk);

    return class AutoTagging extends React.PureComponent<IProps, IState> {
        private isDirty: (a: IAutoTaggingResponse, b: Partial<IAutoTaggingResponse>) => boolean;
        private _mounted: boolean;
        private semaphoreFields = superdesk.instance.config.semaphoreFields ?? { entities: {}, others: {} };
        private replaceAmpersand(input: string) {
            return input.replace(/&/g, 'and');
        }

        constructor(props: IProps) {
            super(props);

            this.state = {
                data: 'not-initialized',
                newItem: null,
                runAutomaticallyPreference: 'loading',
                vocabularyLabels: null,
                tentativeTagName: '',
                forceRenderKey: Math.random(),
                log: '',
            };

            this._mounted = false;
            this.runAnalysis = this.runAnalysis.bind(this);
            this.initializeData = this.initializeData.bind(this);
            this.updateTags = this.updateTags.bind(this);
            this.createNewTag = this.createNewTag.bind(this);
            this.insertTagFromSearch = this.insertTagFromSearch.bind(this);
            this.reload = this.reload.bind(this);
            this.save = this.save.bind(this);
            this.isDirty = memoize((a, b) => Object.keys(generatePatch(a, b)).length > 0);
        }

        runAnalysis() {
            const dataBeforeLoading = this.state.data;

            this.setState({ data: 'loading' }, () => {
                console.log('Article properties:', this.props.article);
                const { guid, language, headline, body_html, extra, slugline } = this.props.article;
                // Apply the ampersand replacement
                const safeHeadline = this.replaceAmpersand(headline);
                const safeSlugline = this.replaceAmpersand(slugline);

                httpRequestJsonLocal<{ analysis: IServerResponse }>({
                    method: 'POST',
                    path: '/ai/',
                    payload: {
                        service: 'semaphore',
                        item: {
                            guid,
                            language,
                            slugline: safeSlugline,
                            headline: safeHeadline,
                            body_html,
                            // headline_extended: extra ? extra.headline_extended : undefined,
                            abstract: extra ? extra.headline_extended : undefined,
                        },
                    },
                }).then((res) => {
                    const resClient = toClientFormat(res.analysis);

                    if (this._mounted) {
                        const existingTags = dataBeforeLoading !== 'loading' && dataBeforeLoading !== 'not-initialized'
                            ? dataBeforeLoading.changes.analysis // keep existing tags
                            : OrderedMap<string, ITagUi>();

                        // Merge new analysis with existing tags
                        const mergedTags = existingTags.merge(resClient);

                        this.setState({
                            data: {
                                original: dataBeforeLoading === 'loading' || dataBeforeLoading === 'not-initialized'
                                    ? { analysis: OrderedMap<string, ITagUi>() } // initialize empty data
                                    : dataBeforeLoading.original, // use previous data
                                changes: { analysis: mergedTags },
                            },
                        });
                    }
                }).catch((error) => {
                    console.error('Error during analysis. We are in runAnalysis:  ', error);

                    if (this._mounted) {
                        this.setState({
                            data: 'not-initialized',
                        });
                    }
                });
            });
        }
        initializeData(preload: boolean) {
            try {
                const existingTags = getExistingTags(this.props.article);
                console.log("existingTags", existingTags);
                // Check if existingTags.subject has any object with scheme value of subject or if organisation or person or event or place or object exists
                // Added check because of destinations and distribution scheme values are present in subject array which causes the empty data to be shown
                if (Object.keys(existingTags).length > 0 &&
                    (existingTags.subject && existingTags.subject.some(s => s.scheme === 'subject')) ||
                    (Array.isArray(existingTags.organisation) && existingTags.organisation.length > 0) ||
                    (Array.isArray(existingTags.person) && existingTags.person.length > 0) ||
                    (Array.isArray(existingTags.event) && existingTags.event.length > 0) ||
                    (Array.isArray(existingTags.place) && existingTags.place.length > 0) ||
                    (Array.isArray(existingTags.object) && existingTags.object.length > 0)) {
                    const resClient = toClientFormat(existingTags);
                    console.log("resClient", resClient);
                    this.setState({
                        data: { original: { analysis: resClient }, changes: { analysis: resClient } },
                    });
                } else if (preload) {
                    this.runAnalysis();
                }
            } catch (error) {
                this.setState({ log: "error" });
                console.error('Error in initializeData:', error);
            }
        }
        updateTags(tags: OrderedMap<string, ITagUi>, data: IEditableData) {
            const { changes } = data;

            this.setState({
                data: {
                    ...data,
                    changes: {
                        ...changes,
                        analysis: tags,
                    },
                },
            });
        }
        createNewTag(newItem: INewItem, data: IEditableData) {
            const _title = newItem.name;

            if (_title == null || newItem.group == null) {
                return;
            }
            // Determine the group kind based on the group value
            const groupKind = newItem.group.value === 'subject' ? 'scheme' : newItem.group.kind;

            const tag: ITagUi = {
                qcode: Math.random().toString(),
                name: _title,
                description: newItem.description,
                source: 'manual',
                creator: "Human",
                relevance: 47,
                altids: {},
                group: {
                    ...newItem.group,
                    kind: groupKind
                },
                scheme: newItem.group.value,
                original_source: 'Human',
            };

            this.updateTags(
                data.changes.analysis.set(tag.qcode, tag),
                data,
            );

            this.setState({ newItem: null });
        }
        insertTagFromSearch(tag: ITagUi, data: IEditableData, searchResponse: IAutoTaggingSearchResult) {
            /**
             * Contains parents of all items returned in search results,
             * not only the one that was eventually chosen
             */
            const parentsMixed = searchResponse?.result?.broader != null
                ? toClientFormat(searchResponse.result.broader)
                : OrderedMap<string, ITagUi>();

            const parentsForChosenTag: Array<ITagUi> = [];

            let latestParent = tag;

            while (latestParent?.parent != null) {
                const nextParent = parentsMixed.get(latestParent.parent);

                if (nextParent != null) {
                    parentsForChosenTag.push(nextParent);
                }

                latestParent = nextParent;
            }

            let result: OrderedMap<string, ITagUi> = data.changes.analysis;

            result = result.set(tag.qcode, tag);

            for (const parent of parentsForChosenTag) {
                // Check if the parent.qcode already exists in the result
                if (!result.has(parent.qcode)) {
                    // If it doesn't exist, add it to the result
                    result = result.set(parent.qcode, parent);
                }
            }

            this.updateTags(
                result,
                data,
            );
            // Reset the autocomplete input
            this.setState({ tentativeTagName: '' });
        }
        getGroupName(group: string, vocabularyLabels: Map<string, string>) {
            return this.semaphoreFields.others[group]?.name ?? vocabularyLabels?.get(group) ?? group;
        }
        reload() {
            this.setState({ data: 'not-initialized' });
            this.initializeData(false);
        }
        // Saves the tags to the article
        save() {
            const { data } = this.state;

            if (data === 'loading' || data === 'not-initialized') {
                return;
            }

            superdesk.entities.article.patch(
                this.props.article,
                createTagsPatch(this.props.article, data.changes.analysis, superdesk),
            ).then(() => {
                this.reload();
                this.sendFeedback(this.props.article, data.changes.analysis);
            });
        }
        sendFeedback(article: IArticle, tags: IAutoTaggingResponse['analysis']): Promise<any> {
            const { guid, language, headline, body_html, extra } = article;

            return httpRequestJsonLocal<{ analysis: IServerResponse }>({
                method: 'POST',
                path: '/ai_data_op/',
                payload: {
                    service: 'semaphore',
                    operation: 'feedback',
                    data: {
                        item: {
                            guid,
                            language,
                            headline,
                            body_html,
                            headline_extended: extra ? extra.headline_extended : undefined,
                        },
                        tags: toServerFormat(tags, superdesk),
                    },
                },
            });
        }
        componentDidMount() {
            this._mounted = true;

            Promise.all([
                getAutoTaggingVocabularyLabels(superdesk),
                preferences.get(RUN_AUTOMATICALLY_PREFERENCE),
                // Need to remove false from the line below to run the analysis automatically
            ]).then(([vocabularyLabels, runAutomatically = false]) => {
                this.setState({
                    vocabularyLabels,
                    runAutomaticallyPreference: runAutomatically,
                });

                this.initializeData(runAutomatically);
            });
        }
        componentWillUnmount() {
            this._mounted = false;
        }
        render() {
            const { runAutomaticallyPreference, vocabularyLabels } = this.state;

            if (runAutomaticallyPreference === 'loading' || vocabularyLabels == null) {
                return null;
            }

            const { data, log } = this.state;
            const dirty = data === 'loading' || data === 'not-initialized' ? false :
                this.isDirty(data.original, data.changes);

            const readOnly = superdesk.entities.article.isLockedInOtherSession(this.props.article);

            return (
                <>
                    {
                        (() => {
                            if (data === 'loading' || data === 'not-initialized') {
                                return null;
                            } else {
                                const treeErrors = arrayToTree(
                                    data.changes.analysis.toArray(),
                                    (item) => item.qcode,
                                    (item) => item.parent,
                                ).errors;

                                // only show errors when there are unsaved changes
                                if (treeErrors.length > 0 && dirty) {
                                    return (
                                        <Alert
                                            type="warning"
                                            size="small"
                                            title={gettext('Autotagger service error')}
                                            message={
                                                gettextPlural(
                                                    treeErrors.length,
                                                    '1 tag can not be displayed',
                                                    '{{n}} tags can not be displayed',
                                                    { n: treeErrors.length },
                                                )
                                            }
                                            actions={[
                                                {
                                                    label: gettext('details'),
                                                    onClick: () => {
                                                        showAutoTaggerServiceErrorModal(superdesk, treeErrors);
                                                    },
                                                    icon: 'info-sign',
                                                },
                                            ]}
                                        />
                                    );
                                } else {
                                    return null;
                                }
                            }
                        })()
                    }

                    <AuthoringWidgetHeading
                        widgetName={label}
                        editMode={dirty}
                    >
                        {
                            data === 'loading' || data === 'not-initialized' || !dirty ? null : (
                                <div>
                                    <button
                                        aria-label="save"
                                        className="btn btn--primary"
                                        onClick={this.save}
                                    >
                                        {gettext('Save')}
                                    </button>

                                    <button
                                        aria-label="cancel"
                                        className="btn"
                                        onClick={this.reload}
                                    >
                                        {gettext('Cancel')}
                                    </button>
                                </div>
                            )
                        }
                    </AuthoringWidgetHeading>
                    <div className="widget-content sd-padding-all--2">
                        <div>
                            {/* Run automatically button is hidden for the next release */}
                            <div className="form__row form__row--flex sd-padding-b--1" style={{ display: 'none' }}>
                                <ButtonGroup align="start">
                                    <Switch
                                        value={runAutomaticallyPreference}
                                        disabled={readOnly}
                                        onChange={() => {
                                            const newValue = !runAutomaticallyPreference;

                                            this.setState({ runAutomaticallyPreference: newValue });

                                            superdesk.preferences.set(RUN_AUTOMATICALLY_PREFERENCE, newValue);

                                            if (newValue && this.state.data === 'not-initialized') {
                                                this.runAnalysis();
                                            }
                                        }}
                                        aria-label="Run automatically"
                                        label={{ content: gettext('Run automatically') }}
                                    />
                                </ButtonGroup>
                            </div>

                            {
                                data === 'loading' || data === 'not-initialized' || log === 'error' ? null : (
                                    <>
                                        <div className="form__row form__row--flex" style={{ alignItems: 'center' }}>
                                            <div style={{ flexGrow: 1 }}>
                                                <Autocomplete
                                                    value={''}
                                                    key={this.state.forceRenderKey}
                                                    keyValue="keyValue"
                                                    items={[]}
                                                    placeholder="Search for an entity or subject"
                                                    search={(searchString, callback) => {
                                                        let cancelled = false;

                                                        httpRequestJsonLocal<IAutoTaggingSearchResult>({
                                                            method: 'POST',
                                                            path: '/ai_data_op/',
                                                            payload: {
                                                                service: 'semaphore',
                                                                operation: 'search',
                                                                data: {
                                                                    searchString,
                                                                    language: this.props.article.language
                                                                },
                                                            },
                                                        }).then((res) => {
                                                            if (cancelled === true) {
                                                                return;
                                                            }

                                                            const json_response = res.result.tags;
                                                            const result_data = res;

                                                            const result = toClientFormat(json_response).toArray();

                                                            const withoutExistingTags = result.filter(
                                                                (searchTag) => !tagAlreadyExists(data, searchTag.qcode),
                                                            );

                                                            const withResponse = withoutExistingTags.map((tag) => ({
                                                                // required for Autocomplete component
                                                                keyValue: tag.name,

                                                                tag,

                                                                // required to get all parents when an item is selected
                                                                entireResponse: result_data,
                                                            }));

                                                            callback(withResponse);
                                                        });

                                                        return {
                                                            cancel: () => {
                                                                cancelled = true;
                                                            },
                                                        };
                                                    }}
                                                    listItemTemplate={(__item: any) => {
                                                        const _item: ITagUi = __item.tag;

                                                        return (
                                                            <div 
                                                                className="auto-tagging-widget__autocomplete-item" 
                                                                aria-label={`Item name ${_item.name}`}
                                                                style={{
                                                                    display: 'flex',
                                                                    flexDirection: 'column',
                                                                    overflow: 'hidden',
                                                                    width: '95%',
                                                                }}
                                                            >
                                                                <b style={{
                                                                    whiteSpace: 'normal',
                                                                    width: '100%',
                                                                    display: 'block',
                                                                    verticalAlign: 'top',
                                                                    wordWrap: 'break-word',
                                                                }}>
                                                                    {_item.name}
                                                                </b>
                                                            </div>

                                                                {
                                                                    _item?.group?.value == null ? null : (
                                                                        <p aria-label={`Group: ${_item.group.value}`}>{_item.group.value}</p>
                                                                    )
                                                                }

                                                                {
                                                                    _item?.description == null ? null : (
                                                                        <p aria-label={`Description: ${_item.description}`}>{_item.description}</p>
                                                                    )
                                                                }
                                                            </div>
                                                        );
                                                    }}
                                                    onSelect={(_value: any) => {
                                                        const tag: ITagUi = _value.tag;
                                                        const entireResponse: IAutoTaggingSearchResult =
                                                            _value.entireResponse;

                                                        this.insertTagFromSearch(tag, data, entireResponse);
                                                        this.setState({
                                                            tentativeTagName: '',
                                                            forceRenderKey: Math.random(),
                                                        });
                                                    }}
                                                    onChange={noop}
                                                />
                                            </div>
                                        </div>
                                        <div className="form__row form__row--flex" style={{ alignItems: 'center' }}>
                                            <Button
                                                aria-label="Add a tag"
                                                type="primary"
                                                size="small"
                                                shape="round"
                                                text={gettext('Add a tag')}
                                                disabled={readOnly}
                                                onClick={() => {
                                                    this.setState({
                                                        newItem: {
                                                            name: '',
                                                        },
                                                    });
                                                }}
                                            />
                                        </div>
                                    </>
                                )
                            }
                        </div>

                        {(() => {
                            if (data === 'loading') {
                                return (
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <div className="spinner-big" />
                                    </div>
                                );
                            } else if (data === 'not-initialized') {
                                return (
                                    <EmptyState
                                        title={gettext('No tags yet')}
                                        description={readOnly ? undefined : gettext('Click "Run" to test Autotagger')}
                                    />
                                );
                            } else if (this.state.log == 'error') {
                                console.error('Error during analysis');
                                return (
                                    <EmptyState
                                        title={gettext('Unable to use Autotagger service')}
                                        description={gettext('Please use the Index field to add tags manually')}
                                    />
                                );
                            } else {
                                const {
                                    entitiesGroupedAndSorted,
                                    othersGrouped,
                                } = getAutoTaggingData(data, this.semaphoreFields);

                                const savedTags = data.original.analysis.keySeq().toSet();

                                let allGrouped = OrderedMap<string, JSX.Element>();

                                othersGrouped.forEach((tags, groupId) => {
                                    console.log('Processing groupId:', groupId);
                                    if (tags != null && groupId != null) {
                                        console.log('tags and groupId are not null');
                                        allGrouped = allGrouped.set(groupId,
                                            <ToggleBoxNext
                                                key={groupId}
                                                title={gettext('Subjects')}
                                                style="circle"
                                                isOpen={true}
                                            >
                                                <TagListComponent
                                                    savedTags={savedTags}
                                                    tags={tags.toMap()}
                                                    readOnly={readOnly}
                                                    // array of qcodes are ids of tags to remove
                                                    onRemove={(ids) => {
                                                        console.log('Removing ids:', ids);
                                                        this.updateTags(
                                                            ids.reduce(
                                                                (analysis, id) => analysis.remove(id),
                                                                data.changes.analysis,
                                                            ),
                                                            data,
                                                        );
                                                    }}
                                                />
                                            </ToggleBoxNext>,
                                        );
                                    } else {
                                        console.log('tags or groupId is null');
                                    }
                                });
                                //  renders the tags in the entities group in the widget window
                                if (entitiesGroupedAndSorted.size > 0) {
                                    allGrouped = allGrouped.set('entities',
                                        <ToggleBoxNext
                                            title={gettext('Entities')}
                                            style="circle"
                                            isOpen={true}
                                            key="entities"
                                        >
                                            {entitiesGroupedAndSorted.map((tags, key) => (
                                                <div key={key}>
                                                    <div
                                                        className="form-label"
                                                        style={{
                                                            display: 'block',
                                                            marginBottom: '5px',
                                                            marginTop: '10px',
                                                        }}
                                                    >
                                                        {groupLabels.get(key).plural}
                                                    </div>
                                                    <TagListComponent
                                                        savedTags={savedTags}
                                                        tags={tags.toMap()}
                                                        readOnly={readOnly}
                                                        onRemove={(ids) => {
                                                            this.updateTags(
                                                                ids.reduce(
                                                                    (analysis, id) => analysis.remove(id),
                                                                    data.changes.analysis,
                                                                ),
                                                                data,
                                                            );
                                                        }}
                                                    />
                                                </div>
                                            )).toArray()}
                                        </ToggleBoxNext>,
                                    );
                                }

                                const allGroupedAndSortedByConfig = allGrouped
                                    .filter((_, key) => hasConfig(key, this.semaphoreFields.others))
                                    .sortBy((_, key) => this.semaphoreFields.others[key].order,
                                        (a, b) => a - b);

                                const allGroupedAndSortedNotInConfig = allGrouped
                                    .filter((_, key) => !hasConfig(key, this.semaphoreFields.others));

                                const allGroupedAndSorted = allGroupedAndSortedByConfig
                                    .concat(allGroupedAndSortedNotInConfig);

                                return (
                                    <React.Fragment>
                                        {
                                            this.state.newItem == null ? null : (
                                                <NewItemComponent
                                                    item={this.state.newItem}
                                                    onChange={(newItem) => {
                                                        this.setState({ newItem });
                                                    }}
                                                    save={(newItem: INewItem) => {
                                                        this.createNewTag(newItem, data);
                                                    }}
                                                    cancel={() => {
                                                        this.setState({ newItem: null });
                                                    }}
                                                    tagAlreadyExists={
                                                        (qcode) => tagAlreadyExists(data, qcode)
                                                    }
                                                />
                                            )
                                        }

                                        <div className="widget-content__main">
                                            {allGroupedAndSorted.map((item) => item).toArray()}
                                        </div>
                                    </React.Fragment>
                                );
                            }
                        })()}
                        <div className="widget-content__footer">
                            {
                                (() => {
                                    if (data === 'loading' || log === 'error') {
                                        return <span />;
                                    } else if (data === 'not-initialized') {
                                        return (
                                            <Button
                                                aria-label="Run"
                                                type="primary"
                                                text={gettext('Run')}
                                                expand={true}
                                                disabled={readOnly}
                                                onClick={() => {
                                                    this.runAnalysis();
                                                }}
                                            />
                                        );
                                    } else {
                                        return (
                                            <Button
                                                aria-label="Refresh"
                                                type="primary"
                                                text={gettext('Refresh')}
                                                expand={true}
                                                disabled={readOnly}
                                                onClick={() => {
                                                    this.runAnalysis();
                                                }}
                                            />
                                        );
                                    }
                                })()
                            }
                        </div>
                    </div>
                </>
            );
        }
    };
}
