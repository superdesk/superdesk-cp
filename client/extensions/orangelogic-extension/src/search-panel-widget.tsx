import * as React from 'react';
import {ISearchPanelWidgetProps, ISuperdesk} from 'superdesk-api';
import {CheckboxButton, Spacer} from 'superdesk-ui-framework/react';

type IMediaType = 'Image' | 'Video';

interface IParams {
    from: string;
    to: string;
    mediaTypes: {
        [key in IMediaType]?: boolean;
    };
};

interface IMediaTypeLabel {
    type: IMediaType,
    label: string;
}

export const searchPanelWidgetFactory = (
    gettext: ISuperdesk['localization']['gettext'],
): React.ComponentType<ISearchPanelWidgetProps<IParams>> => {
    const mediaTypes: Array<IMediaTypeLabel> = [
        {
            type: 'Image',
            label: gettext('Picture'),
        },
        {
            type: 'Video',
            label: gettext('Video'),
        },
    ];

    return class SearchPanelWidget extends React.PureComponent<ISearchPanelWidgetProps<IParams>> {
        toggleMediaType(type: IMediaType) {
            const mediaTypes = this.props.params.mediaTypes || {};

            mediaTypes[type] = !mediaTypes[type];
            this.props.setParams({mediaTypes});
        }

        isActive(type: IMediaType) {
            return this.props.params.mediaTypes != null && this.props.params.mediaTypes[type] === true;
        }

        render() {
            const {params} = this.props;

            if (this.props.provider !== 'orangelogic') {
                return null;
            }

            return (
                <fieldset>
                    <div className="field sd-margin-t--2">
                        <Spacer h gap={'4'}>
                            {mediaTypes.map((type, i) => (
                                <CheckboxButton key={i} checked={this.isActive(type.type)} label={{text: type.label}} onChange={() => this.toggleMediaType(type.type)} />
                            ))}
                        </Spacer>
                    </div>                 
                    <div className="field">
                        <label className="search-label">{gettext('From')}</label>
                        <input type="date" value={params.from || ''}
                            onChange={(event) => this.props.setParams({from: event.target.value})}
                        />
                    </div>
                    <div className="field">
                        <label className="search-label">{gettext('To')}</label>
                        <input type="date" value={params.to || ''}
                            onChange={(event) => this.props.setParams({to: event.target.value})}
                        />
                    </div>
                </fieldset>
            );
        }
    };
};
