/**
 * This is the default configuration file for the Superdesk application. By default,
 * the app will use the file with the name "superdesk.config.js" found in the current
 * working directory, but other files may also be specified using relative paths with
 * the SUPERDESK_CONFIG environment variable or the grunt --config flag.
 */
module.exports = function(grunt) {
    return {
        apps: [
            'superdesk.analytics',
            'superdesk-planning',
        ],
        importApps: [
            '../index',
            'superdesk-analytics',
            'superdesk-planning',
        ],
        defaultRoute: '/workspace/monitoring',

        defaultTimezone: 'America/Toronto',

        view: {
            timeformat: 'HH:mm',
            dateformat: 'DD.MM.YYYY',
        },

        editor3: { browserSpellCheck: true, },
        
        langOverride: {
            'en': {
                'Dateline': 'Placeline',
                'Take Key': 'Writethru',
                'update': '1st Writethru',
                '2nd update': '2nd Writethru',
                '3rd update': '3rd Writethru',
                '4th update': '4th Writethru',
                '5th update': '5th Writethru',
                '6th update': '6th Writethru',
                '7th update': '7th Writethru',
                '8th update': '8th Writethru',
                '9th update': '9th Writethru',
                '10th update': '10th Writethru',
                '11th update': '11th Writethru',
                '12th update': '12th Writethru',
                '13th update': '13th Writethru',
                '14th update': '14th Writethru',
                '15th update': '15th Writethru',
                '16th update': '16th Writethru',
                '17th update': '17th Writethru',
                '18th update': '18th Writethru',
                '19th update': '19th Writethru',
                '20th update': '20th Writethru'
            },
            'fr_CA': {
                'Take Key': 'Lead',
                'update': '1er Lead',
                '2nd update': '2e Lead',
                '3rd update': '3e Lead',
                '4th update': '4e Lead',
                '5th update': '5e Lead',
                '6th update': '6e Lead',
                '7th update': '7e Lead',
                '8th update': '8e Lead',
                '9th update': '9e Lead',
                '10th update': '10e Lead',
                '11th update': '11e Lead',
                '12th update': '12e Lead',
                '13th update': '13e Lead',
                '14th update': '14e Lead',
                '15th update': '15e Lead',
                '16th update': '16e Lead',
                '17th update': '17e Lead',
                '18th update': '18e Lead',
                '19th update': '19e Lead',
                '20th update': '20e Lead'
            }      
        },

        features: {
            preview: 1,
            customAuthoringTopbar: {
                toDesk: true,
                publish: true,
                publishAndContinue: true,
            },
            swimlane: {defaultNumberOfColumns: 4},
            editor3: true,
            validatePointOfInterestForImages: true,
            editorHighlights: true,
            editFeaturedImage: true,
            searchShortcut: true,
            elasticHighlight: true,
            hideCreatePackage: true,
            useTansaProofing: true,
            planning: true,
            noPublishOnAuthoringDesk: true,
            autorefreshContent: true,
        },
        
        item_profile: {
            change_profile: 1
        },

        workspace: {
            analytics: true,
            planning: true,
            assignments: true,
        },
        
        search_cvs: [
            {id: 'categories', name:'Wire', field: 'anpa_category', list: 'categories'},
            {id: 'subject_custom', name:'Index', field: 'subject', list: 'subject_custom'},
            {id: 'distribution', name:'Services', field: 'subject', list: 'distribution'},
            {id: 'language', name:'Language', field: 'language', list: 'languages'},
            {id: 'tag', name:'Tag', field: 'subject', list: 'tag'}
        ],
        
        search: {
            'slugline': 1,
            'headline': 1,
            'unique_name': 1,
            'story_text': 1,
            'byline': 1,
            'keywords': 0,
            'creator': 1,
            'from_desk': 1,
            'to_desk': 1,
            'spike': 1,
            'ingest_provider': 1,
            'marked_desks': 1,
            'scheduled': 1
        },
        
        list: {
            priority: [
                'urgency'
            ],
            firstLine: [
                'slugline',  
                'takekey',
                'highlights',
                'markedDesks',
                'headline',
                'associations',
                'versioncreated'
            ],
            secondLine: [
                'language',
                'state',
                'update',
                'scheduledDateTime',
                'embargo',
                'signal',
                'broadcast',
                'flags',
                'updated',
                'provider',
                'desk',
                'fetchedDesk',
                'translations',
                'assignment',
                'associatedItems',
                'used'
            ]
        },        

        monitoring: {
            scheduled: {
                sort: {
                    default: { field: 'publish_schedule', order: 'asc' },
                    allowed_fields_to_sort: [ 'publish_schedule' ]
                }
            },
        }        
    };
};
