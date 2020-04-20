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
        defaultRoute: '/workspace/personal',

        view: {
            timeformat: 'HH:mm',
            dateformat: 'DD.MM.YYYY',
        },

        features: {
            preview: 1,
            swimlane: {defaultNumberOfColumns: 4},
            editor3: true,
            validatePointOfInterestForImages: true,
            editorHighlights: true,
            editFeaturedImage: false,
            searchShortcut: true,
            useTansaProofing: true,
            planning: true,
        },

        workspace: {
            analytics: true,
            planning: true,
            assignments: true,
        },
        
        search: {
            'slugline': 1,
            'headline': 1,
            'short_headline': 1,
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
                'rewrite_sequence', 
                'takekey',
                'highlights',
                'markedDesks',
                'headline',
                'associations',
                'versioncreated'
            ],
            secondLine: [
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
                'associatedItems',
                'translations',
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
