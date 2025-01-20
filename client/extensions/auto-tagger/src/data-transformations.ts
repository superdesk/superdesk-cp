import {IArticle, ISuperdesk, ISubject} from 'superdesk-api';
import {OrderedMap} from 'immutable';
import {ITagUi} from './types';
import {getServerResponseKeys, toServerFormat, ITagBase, ISubjectTag, IServerResponse} from './adapter';

export function createTagsPatch(
    article: IArticle,
    tags: OrderedMap<string, ITagUi>,
    superdesk: ISuperdesk,
): Partial<IArticle> {
    const serverFormat = toServerFormat(tags, superdesk);
    const patch: Partial<IArticle> = {};

    // Helper functions
    const isValidTag = (tag: ISubject | undefined, qcode: string | undefined): tag is ISubject => {
        return !!tag && !!qcode && typeof tag.qcode === 'string';
    };

    const isPreservedScheme = (scheme: string | undefined): boolean => {
        const preservedSchemes = ['destinations', 'distribution'];
        return preservedSchemes.includes(scheme ?? '');
    };

    // Create a duplicate tag for the index field by:
    // Overriding the scheme to 'subject_custom' to make it appear in the index field
    // Using the same qcode ensures we can track and update the same tag in both places
    const createIndexTag = (tag: ISubject): ISubject => ({ ...tag, scheme: 'subject_custom' });

    getServerResponseKeys().forEach((key) => {
        // Initialize maps
        let oldValues = OrderedMap<string, ISubject>(
            (article[key] || [])
                .filter((_item) => typeof _item.qcode === 'string')
                .map((_item) => [_item.qcode, _item])
        );
        let newValuesMap = OrderedMap<string, ISubject>();
        const newValues = serverFormat[key];
        // Check if a tag should be removed
        const wasRemoved = (tag: ISubject) => oldValues.has(tag.qcode) && !newValuesMap.has(tag.qcode);

        // Preserve existing tags with special schemes
        oldValues?.forEach((tag, qcode) => {
            if (isValidTag(tag, qcode) && isPreservedScheme(tag.scheme)) {
                newValuesMap = newValuesMap.set(qcode as string, tag);
            }
        });

        // Add new tags and their index versions
        newValues?.forEach((tag) => {
            if (isValidTag(tag, tag.qcode)) {
                // Add original tag
                newValuesMap = newValuesMap.set(tag.qcode, tag);
                // Add index tag
                newValuesMap = newValuesMap.set(tag.qcode, createIndexTag(tag));
            }
        });

        // Create final array of tags
        patch[key] = oldValues
            .merge(newValuesMap)
            .filter((tag) => !wasRemoved(tag))
            .toArray();
    });

    return patch;
}

export function getExistingTags(article: IArticle): IServerResponse {
    const result: IServerResponse = {};

    getServerResponseKeys().forEach((key) => {
        const values = article[key] ?? [];

        if (key === 'subject') {
            if (values.length > 0) {
                result[key] = values
                .filter(subjectItem => subjectItem.scheme != null) // Only include items with a scheme
                .map(subjectItem => {
                    const {
                        name,
                        description,
                        qcode,
                        source,
                        altids,
                        scheme,
                        aliases,
                        original_source,
                        parent,
                        relevance,
                        creator
                    } = subjectItem;

                    const subjectTag: ISubjectTag = {
                        name,
                        description,
                        qcode,
                        source,
                        altids: altids ?? {},
                        parent,
                        scheme,
                        aliases,
                        original_source,
                        relevance,
                        creator
                    };
                    return subjectTag;
                });
            }
        } else if (values.length > 0) {
            result[key] = values.map((entityItem) => {
                const {
                    name,
                    description,
                    qcode,
                    source,
                    altids,
                    scheme,
                    aliases,
                    original_source,
                    parent,
                    relevance,
                    creator
                } = entityItem;

                const entityTag: ITagBase = {
                    name,
                    description,
                    qcode,
                    source,
                    altids: altids ?? {},
                    parent,
                    scheme,
                    aliases,
                    original_source,
                    relevance,
                    creator
                };
                return entityTag;
            });
        }
    });

    return result;
}
