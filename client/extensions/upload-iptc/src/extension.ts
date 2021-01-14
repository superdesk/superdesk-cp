import {IExtension, IExtensionActivationResult, ISuperdesk, IArticle, ISubject} from 'superdesk-api';

const PHOTO_CAT_ID = 'photo_categories';
const PHOTO_SUPPCAT_ID = 'photo_supplementalcategories';

// convert 20191209 to 2019-12-09
const parseDate = (date: string) => date.length === 8 ?
    [
        date.substr(0, 4),
        date.substr(4, 2),
        date.substr(6, 2),
    ].join('-') : date;

// convert 152339+0000 to 15:23:39+0000
const parseTime = (time: string) => time.length >= 6 ?
    [
        time.substr(0, 2),
        time.substr(2, 2),
        time.substr(4),
    ].join(':') : time;

const parseDatetime = (date?: string, time?: string) => (date && time) ?
    `${parseDate(date)}T${parseTime(time)}` :
    null;

const copySubj = (scheme: string) => (subj: ISubject) => ({
    name: subj.name,
    qcode: subj.qcode,
    scheme: scheme,
    translations: subj.translations,
    source: '',
});

const extension: IExtension = {
    id: 'upload-iptc',
    activate: (superdesk: ISuperdesk) => {
        const result: IExtensionActivationResult = {
            contributions: {
                iptcMapping: (data, item: IArticle) => Promise.all([
                    superdesk.entities.vocabulary.getVocabulary(PHOTO_CAT_ID),
                    superdesk.entities.vocabulary.getVocabulary(PHOTO_SUPPCAT_ID),
                ]).then(([categories, supp_categories]: [Array<ISubject>, Array<ISubject>]) => {
                    Object.assign(item, {
                        slugline: data.ObjectName,
                        byline: data['By-line'],
                        headline: data.Headline,
                        ednote: data.SpecialInstructions,

                        original_source: data.Source,
                        creditline: data.Credit,
                        copyrightnotice: data.CopyrightNotice,
                        language: data.LanguageIdentifier || 'en',
                        keywords: data.SubjectReference ? data.SubjectReference.split('\n').map((keyword: string) => keyword.trim()) : [],
                        subject: (item.subject || []).concat(
                            data.Category != null ?
                                categories.filter((subj) => subj.qcode === data.Category).map(copySubj(PHOTO_CAT_ID)) :
                                [],
                            data.SupplementalCategories != null ?
                                supp_categories.filter((subj) => subj.qcode === data.SupplementalCategories).map(copySubj(PHOTO_SUPPCAT_ID)) :
                                [],
                        ),
                        dateline: {
                            text: [
                                data.City,
                                data['Province-State'],
                                data['Country-PrimaryLocationName'],
                            ].filter((x) => !!x).join(', '),
                            located: {
                                city: data.City,
                                state: data['Province-State'],
                                country: data['Country-PrimaryLocationName'],
                                country_code: data['Country-PrimaryLocationCode'],
                            },
                        },
                        extra: {
                            filename: data.OriginalTransmissionReference,
                            photographer_code: data['By-lineTitle'],
                            caption_writer: data['Writer-Editor'],
                        },
                    });

                    if (item.extra) {
                        const created = parseDatetime(data.DateCreated, data.TimeCreated || '000000');
                        const release = parseDatetime(data.ReleaseDate, data.ReleaseTime);

                        if (created && created !== '') {
                            item.firstcreated = created;
                        }

                        if (release) {
                            item.extra.DateRelease = release;
                        }
                    }

                    console.debug('iptc', data, item);

                    return item;
                }),
            },
        };

        return Promise.resolve(result);
    },
};

export default extension;
