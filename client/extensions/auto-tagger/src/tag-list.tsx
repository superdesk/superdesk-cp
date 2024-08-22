import * as React from 'react';
import {Set, OrderedMap} from 'immutable';
import {ISuperdesk, ITreeNode} from 'superdesk-api';
import {ITagUi} from './types';
import {Tag} from 'superdesk-ui-framework/react';
import {TagPopover} from './tag-popover';
import {noop} from 'lodash';

interface IProps {
    readOnly: boolean;
    savedTags: Set<string>;
    tags: OrderedMap<string, ITagUi>;
    inline?: boolean;
    onRemove(id: Array<string>): void;
}

export function getTagsListComponent(superdesk: ISuperdesk): React.ComponentType<IProps> {
    const {gettext} = superdesk.localization;
    const {arrayToTree, treeToArray} = superdesk.utilities;

    return class TagList extends React.PureComponent<IProps> {
        render() {
            const {tags, onRemove, readOnly, savedTags, inline} = this.props;
            const tagsJs: Array<ITagUi> = Object.values(tags.toJS());

            const tagsTree = arrayToTree(
                tagsJs,
                (item) => item.qcode,
                (item) => item.parent,
            ).result;

            const tagListItem = (node: ITreeNode<ITagUi>) => {
                const isRootNodeWithChildren = node.parent == null && node.children != null;
                const isNodeEntity = node.parent == null && node.children == null;
                const item = node.value;

                return (
                    <TagPopover
                        tag={item}
                        key={item.qcode}
                        gettext={gettext}

                        // root items with children have to be on a separate line
                        display={isRootNodeWithChildren && !inline ? 'block' : undefined}
                    >
                        <Tag
                            key={item.qcode}
                            text={item.name}
                            readOnly={readOnly}
                            shade={savedTags.has(item.qcode) && !readOnly ?
                                (isRootNodeWithChildren ? 'highlight2' : 'highlight1') :
                                (isRootNodeWithChildren ? 'darker' : 'light')}
                            onClick={
                                readOnly
                                    ? noop
                                    : () => {
                                        if (isNodeEntity) {
                                            onRemove([node.value.qcode]);
                                        } else {
                                            onRemove(
                                                treeToArray([node]).map(({qcode}) => qcode),
                                            );
                                        }
                                    }
                            }
                        />
                    </TagPopover>
                );
            };

            function renderTreeNode(treeNodes: Array<ITreeNode<ITagUi>>, level: number = 0): JSX.Element {
                const treeNodesMap = treeNodes.map((node) => (
                    <div key={node.value.qcode} style={{paddingLeft: level * 14}}>
                        {tagListItem(node)}
                        {node.children != null && renderTreeNode(node.children, level + 1)}
                    </div>
                ));

                return <div>{treeNodesMap}</div>;
            }

            return renderTreeNode(tagsTree);
        }
    };
}
