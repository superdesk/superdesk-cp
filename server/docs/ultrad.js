'use strict';
const Document = require('../../schema/Document');
const {viewableStates} = require('../../schema/DocumentState');
const documentFlow = require('../../services/document.flow');
const {importFromXml, exportToXml} = require('../../services/impex');
const documentRouter = require('express').Router();
const upload = require('../upload-handler');

documentRouter.post(
    '/',
    function createDocument(req, res, next) {
        const document = new Document(req.body);

        document.createdAt = document.updatedAt = new Date();

        document.save()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.post(
    '/import',
    upload.single('jimiXml'),
    function createDocumentFromXML(req, res, next) {
        const {file} = req;

        if (!file || file.buffer.length < 1) {
            return next(ERRORS.badRequest('upload.missingData'));
        }

        const importedDocument = importFromXml(file.buffer);

        const document = new Document(importedDocument);

        document.createdAt = document.updatedAt = new Date();

        document.save()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.post(
    '/search',
    function createDocument(req, res, next) {

        const {query} = req.body;

        Document.find()
            .fullTextSearch(query)
            .exec()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.get(
    '/me',
    function findMyDocs(req, res, next) {
        Document.find({assignedTo: req.auth.user_id, state: {$in: viewableStates}})
            .sort({updatedAt: -1})
            .exec()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.get(
    '/',
    function listDocuments(req, res, next) {
        const query = {};

        if ('state' in req.query) {
            query.state = req.query.state;
        }

        Document.find(query)
            .sort({updatedAt: -1})
            .exec()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.get(
    '/:id',
    function getSingleDocument(req, res, next) {
        Document.findOne({_id: req.params.id})
            .deepPopulate(['lexicalIndexes', 'lexicalIndexes.parent'])
            .exec()
            .then((result) => res.json(result))
            .catch(next);
    }
);

documentRouter.get(
    '/:id/export',
    function getSingleDocument(req, res, next) {
        Document.findOne({_id: req.params.id})
            .exec()
            .then((doc) => {
                if (!doc.exportTemplate) {
                    throw ERRORS.badData('Was not imported from JIMI');
                }

                return res.send(exportToXml(doc));
            })
            .catch(next);
    }
);

documentRouter.put(
    '/:id',
    function updateDocument(req, res, next) {
        const document = new Document(req.body);
        document.updatedAt = new Date();

        document.validate()
            .then(() => Document.findByIdAndUpdate(req.params.id, document))
            .then(res.json.bind(res))
            .catch(next);
    }
);

[
    ['assign', documentFlow.assignDocument],
    ['submit', documentFlow.submitDocumentForReview],
    ['approve', documentFlow.approveDocument],
    ['export', documentFlow.exportDocument],
    ['archived', documentFlow.archiveDocument]
].forEach(([action, fn]) => {
    documentRouter.put(
        `/:id/${action}`,
        function (req, res, next) {
            fn(req.params.id).then(doc => res.json(doc)).catch(next);
        }
    );
});

module.exports = documentRouter;
